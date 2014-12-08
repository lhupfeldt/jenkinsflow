window.onload=function(){
    var links = [];
    var nodes = [];
    var job_urls = []
    var svg = d3.select("svg");

    d3.json("http://localhost:9090/jenkinsflow/flow_graph.json", function(error, json) {
      if (error) {
          console.error(error.message);
      } else {
          links = json["links"];
          nodes = json["nodes"];
          job_urls =json["nodes"].map(function(s) {
            return s.url;
          });
          var dgrph = new dagreD3.graphlib.Graph().setGraph({
              nodesep: 50,
              ranksep: 70,
              rankdir: "TD",
              marginx: 20,
              marginy: 20
          });

          nodes.forEach(function(node) {
              // Calculate the size of the node
              var text = svg.append("svg:text")
                  .attr("x", "-200")
                  .attr("y", "-200")
                  .text(node.name)
              var t_width = text.node().getBBox().width;
              text.remove();

              dgrph.setNode(node.id, {
                  label: node.name,
                  width: t_width
              });
          });

          links.forEach(function(link) {
              dgrph.setEdge(link.source, link.target, {
                  arrowhead: "vee"
              });
          });

          var render = new dagreD3.render();
          var container = d3.select("svg g");

          render(container, dgrph);
        }
    });

};
