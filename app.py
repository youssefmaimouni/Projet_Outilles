from flask import Flask, render_template, request, flash, redirect, url_for
import networkx as nx
import matplotlib
matplotlib.use('Agg')  # Nécessaire pour Flask
import matplotlib.pyplot as plt
import io
import base64
import os
from urllib.parse import unquote

# Initialisation de l'application Flask
app = Flask(__name__)

# Configuration (à remplacer par une vraie clé en production)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or 'dev_key_12345'

def create_transport_graph(routes):
    """Crée un graphe orienté pondéré à partir des routes"""
    G = nx.DiGraph()
    for route in routes:
        try:
            from_city = route['from'].strip().title()
            to_city = route['to'].strip().title()
            capacity = int(route['capacity'])
            cost = float(route['cost'])
            
            G.add_edge(from_city, to_city, capacity=capacity, cost=cost)
        except (ValueError, KeyError) as e:
            flash(f"Erreur dans la route {route.get('from')}→{route.get('to')}: {str(e)}", 'error')
            continue
    return G

def plot_network(graph, solution):
    """Génère une visualisation du graphe et retourne l'image en base64"""
    plt.figure(figsize=(12, 8))
    fig, ax = plt.subplots(figsize=(12, 8))  # Ajout d'un axe

    pos = nx.spring_layout(graph, k=0.5, iterations=50)

    # Dessin des nœuds
    nx.draw_networkx_nodes(graph, pos, node_color='lightblue', node_size=800, ax=ax)
    nx.draw_networkx_labels(graph, pos, font_size=10, font_weight='bold', ax=ax)

    # Arêtes utilisées et non utilisées
    used_edges = [(u, v) for (u, v) in graph.edges() if solution.get((u, v), 0) > 0]
    unused_edges = [(u, v) for (u, v) in graph.edges() if solution.get((u, v), 0) == 0]

    # Arêtes non utilisées (grises)
    nx.draw_networkx_edges(
        graph, pos, edgelist=unused_edges,
        edge_color='gray', width=1, alpha=0.3,
        arrowstyle='-|>', arrows=True, arrowsize=20, ax=ax
    )

    # Arêtes utilisées (en rouge ou autre)
    nx.draw_networkx_edges(
        graph, pos, edgelist=used_edges,
        edge_color='red', width=2,
        arrowstyle='-|>', arrows=True, arrowsize=20, ax=ax
    )

    # Étiquettes des arêtes
    edge_labels = {}
    for (u, v), data in graph.edges.items():
        flow = solution.get((u, v), 0)
        edge_labels[(u, v)] = f"{flow}/{data['capacity']}\n(${data['cost']})"

    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=8, label_pos=0.3, ax=ax)

    ax.set_title("Solution d'Optimisation du Réseau", pad=20)
    ax.axis('off')
    plt.tight_layout()

    # Image base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def plot_solution(graph, solution):
    """Génère une visualisation du graphe avec les chemins utilisés en rouge"""
    plt.figure(figsize=(12, 8))
    
    # Positionnement des nœuds
    pos = nx.spring_layout(graph, k=0.8, iterations=50, seed=42)  # Seed pour reproductibilité
    
    # Dessin des nœuds
    nx.draw_networkx_nodes(graph, pos, node_color='lightblue', node_size=800, alpha=0.9)
    nx.draw_networkx_labels(graph, pos, font_size=10, font_weight='bold')
    
    # Séparation des arêtes utilisées et non utilisées
    used_edges = [(u, v) for (u, v) in graph.edges() if solution.get((u, v), 0) > 0]
    unused_edges = [(u, v) for (u, v) in graph.edges() if (u, v) not in used_edges]
    
    # Dessin des arêtes non utilisées (en gris)
    nx.draw_networkx_edges(graph, pos, edgelist=unused_edges,
                         edge_color='gray', width=1, alpha=0.4,
                         arrowstyle='-|>', arrowsize=12)
    
    # Dessin des arêtes utilisées (en rouge avec épaisseur variable)
    for u, v in used_edges:
        flow_ratio = solution.get((u, v), 0) / graph[u][v]['capacity']
        edge_width = 1 + 4 * flow_ratio  # Largeur proportionnelle au flot
        
        nx.draw_networkx_edges(graph, pos, edgelist=[(u, v)],
                             edge_color='red', width=edge_width, alpha=0.8,
                             arrowstyle='-|>', arrowsize=15)
    
    # Étiquettes des arêtes (seulement pour les arêtes utilisées)
    edge_labels = {
        (u, v): f"{solution.get((u, v), 0)}/{graph[u][v]['capacity']}\n(${graph[u][v]['cost']})"
        for u, v in used_edges
    }
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels,
                               font_size=8, label_pos=0.4, bbox=dict(alpha=0.7))
    
    # Titre et légende
    plt.title("Solution d'Optimisation - Chemins utilisés (rouge)", pad=20, fontsize=14)
    plt.axis('off')
    
    # Ajout d'une légende manuelle
    plt.figtext(0.5, 0.01, 
               "Flèches rouges: chemins utilisés (épaisseur proportionnelle au flot)\n"
               "Flèches grises: chemins non utilisés",
               ha="center", fontsize=10, bbox=dict(facecolor='white', alpha=0.5))
    
    plt.tight_layout()
    
    # Conversion en image base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    plt.close()
    return base64.b64encode(buf.read()).decode('utf-8')

def prepare_network_data(graph, solution):
    """Prépare les données pour la visualisation D3.js"""
    return {
        'nodes': [{'id': n, 'name': n} for n in graph.nodes()],
        'links': [{
            'source': u,
            'target': v,
            'capacity': data['capacity'],
            'cost': data['cost'],
            'flow': solution.get((u, v), 0)
        } for u, v, data in graph.edges(data=True)]
    }

def build_paths(G, flow_dict):
    paths = []
    for u in flow_dict:
        for v in flow_dict[u]:
            if flow_dict[u][v] > 0:
                paths.append({
                    'path': f"{u} → {v}",
                    'flow': flow_dict[u][v],
                    'capacity': G[u][v]['capacity'],
                    'utilization': f"{(flow_dict[u][v]/G[u][v]['capacity'])*100:.1f}%",
                    'cost': G[u][v]['cost'],
                    'total_cost': flow_dict[u][v] * G[u][v]['cost']
                })
    return paths

def find_used_paths(source, target, flow_dict):
    paths = []

    def dfs(u, path):
        if u == target:
            paths.append(path)
            return
        for v, flow in flow_dict[u].items():
            if flow > 0 and v not in path:
                dfs(v, path + [v])

    dfs(source, [source])
    return paths

def extract_optimal_path(flow_dict, source, target):
    """Retourne un chemin unique de source à target basé sur les flots positifs."""
    path = []
    current = source
    visited = set()

    while current != target:
        visited.add(current)
        found = False
        for neighbor, flow in flow_dict[current].items():
            if flow > 0 and neighbor not in visited:
                path.append((current, neighbor))
                current = neighbor
                found = True
                break
        if not found:
            break  # Chemin bloqué

    return [source] + [v for u, v in path]



@app.route('/', methods=['GET'])
def main():
    return render_template('index.html')

@app.route('/form', methods=['GET', 'POST'])
def transport_optimization():
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            source = request.form.get('source', '').strip().title()
            target = request.form.get('target', '').strip().title()
            algorithm = request.form.get('algorithm', 'max_flow')
            
            # Construction des routes
            routes = []
            from_cities = request.form.getlist('from_city')
            to_cities = request.form.getlist('to_city')
            capacities = request.form.getlist('capacity')
            costs = request.form.getlist('cost')
            
            for i in range(len(from_cities)):
                routes.append({
                    'from': from_cities[i],
                    'to': to_cities[i],
                    'capacity': capacities[i],
                    'cost': costs[i]
                })

            # Validation des données
            if not all([source, target]):
                flash("Veuillez spécifier une source et une destination", 'error')
                return render_template('form.html', 
                                    routes=routes, 
                                    source=source, 
                                    target=target, 
                                    algorithm=algorithm)
            
            if not routes:
                flash("Veuillez ajouter au moins une route", 'error')
                return render_template('form.html', 
                                    source=source, 
                                    target=target, 
                                    algorithm=algorithm)

            # Création du graphe
            G = create_transport_graph(routes)
            
            # Vérification des villes source/destination
            missing = []
            if source not in G:
                missing.append(source)
            if target not in G:
                missing.append(target)
            
            if missing:
                flash(f"Ville(s) non définie(s): {', '.join(missing)}", 'error')
                return render_template('form.html', 
                                    routes=routes, 
                                    source=source, 
                                    target=target, 
                                    algorithm=algorithm)

            # Calcul selon l'algorithme choisi
            if algorithm == 'max_flow':
                flow_value, flow_dict = nx.maximum_flow(G, source, target)
                value = flow_value
                result_type = "Flot Maximal (Ford-Fulkerson)"

            elif algorithm == 'min_cost':
                flow_dict = nx.max_flow_min_cost(G, source, target)
                value = nx.cost_of_flow(G, flow_dict)
                result_type = "Coût Minimal"

            elif algorithm == 'edmonds_karp':
                flow_value, flow_dict = nx.maximum_flow(G, source, target, flow_func=nx.algorithms.flow.edmonds_karp)
                value = flow_value
                result_type = "Flot Maximal (Edmonds_Karp)"
            
            elif algorithm == 'push_relabel':
                flow_value, flow_dict = nx.maximum_flow(G, source, target, flow_func=nx.algorithms.flow.preflow_push)
                value = flow_value
                result_type = "Flot Maximal (Push-Relabel)"


            paths = build_paths(G, flow_dict)
            plot_url = plot_network(G, flow_dict)
            network_data = prepare_network_data(G, flow_dict)
            used_paths = find_used_paths(source, target, flow_dict)
            optimal_path_nodes = extract_optimal_path(flow_dict, source, target)
            optimal_path_str = " → ".join(optimal_path_nodes)
            print(optimal_path_nodes)

            return render_template('results.html',
                                plot_url=plot_url,
                                network_data=network_data,
                                result_type=result_type,
                                value=value,
                                paths=paths,
                                algorithm=algorithm,
                                used_paths=used_paths,
                                source=source,
                                target=target,
                                optimal_path_str=optimal_path_str)


        except nx.NetworkXError as e:
            flash(f"Erreur dans le calcul: {str(e)}", 'error')
        except Exception as e:
            flash(f"Erreur inattendue: {str(e)}", 'error')

    return render_template('form.html')

@app.route('/favicon.ico')
def favicon():
    return '', 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)