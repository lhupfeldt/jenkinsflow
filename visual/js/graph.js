window.onload=function(){
    var nodePadding = 10;
 
    var links;
    var nodes;
    var job_urls = []
 
    d3.json("http://localhost:9090/jenkinsflow/flow_graph.json", function(error, json) {
          if (error) {
              console.error(error.message);
          } else {
              links = json["links"];
              nodes = json["nodes"];
              job_urls =json["nodes"].map(function(s) {
                return s.url;
              });
              update(links, nodes);
          }
      }
    );
    
    var g = new dagreD3.graphlib.Graph().setGraph({
        nodesep: 10,
        ranksep: 70,
        rankdir: "TD",
        marginx: 20,
        marginy: 20
    });   

    nodes.forEach(function(node) {
        g.setNode(node.id, {
            label: node.name,
            width: 100
        });
    });
      
    links.forEach(function(link) {
        g.setEdge(link.source, link.target, {
            arrowhead: "vee"
        });
    });
      
    var render = new dagreD3.render();
    var container = d3.select("svg g");
      
    render(container, g);
};
