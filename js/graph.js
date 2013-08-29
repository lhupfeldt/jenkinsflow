window.onload=function(){
    /*
    Object.prototype.getName = function() { 
       var funcNameRegex = /function (.{1,})\(/;
          var results = (funcNameRegex).exec((this).constructor.toString());
             return (results && results.length > 1) ? results[1] : "";
    };
    */
  var nodePadding = 10;

  var links;
  var nodes;

  d3.json("http://localhost:9090/jenkinsflow/flow_graph.json", function(error, json) {
        if (error) {
            console.error(error);
        } else {
            links = json["links"];
            nodes = json["nodes"]
            update(links, nodes);
        }
    }
  );

function refreshBuilds(url) {
    var f = function() {
        new Ajax.Request(url, {
            onSuccess: function(rsp) {
                console.debug(rsp.responseJSON);
                jsn = rsp.responseJSON;
                console.debug(jsn);
                nodes.forEach(function (n) {
                    d3.select("#node-" + n.label + ">rect").style("fill", "#fff");
                })
                jsn.forEach(function (j) {
                    var selected = d3.select("#node-" + j.job + ">rect");
                    console.debug(selected);
                    selected.style("fill", "blue");
                })
                console.debug("Before update in json");
                refreshBuilds(url);
            }
        });
    };
    window.setTimeout(f, 2000);
}

function update(links, b_nodes) {
  function spline(e) {
      var points = e.dagre.points.slice(0);
      var source = dagre.util.intersectRect(e.source.dagre, points[0]);
      var target = dagre.util.intersectRect(e.target.dagre, points[points.length - 1]);
      points.unshift(source);
      points.push(target);
      return d3.svg.line()
          .x(function (d) {
          return d.x;
      })
          .y(function (d) {
          return d.y;
      })
          .interpolate("linear")
      (points);
  }

  // Translates all points in the edge using `dx` and `dy`.
  function translateEdge(e, dx, dy) {
      e.dagre.points.forEach(function (p) {
          p.x = Math.max(0, Math.min(svgBBox.width, p.x + dx));
          p.y = Math.max(0, Math.min(svgBBox.height, p.y + dy));
      });
  }

  // Get the data in the right form
  console.debug('before links')
  links.forEach(function (d) {
      console.debug('links d')
      console.debug(d)
      // If we are being called first time
      var source = b_nodes.filter(function(node){return node.id == d.source;})[0],
          target = b_nodes.filter(function(node){return node.id == d.target;})[0]
      if (source.edges == undefined) {
          source['label'] = d.source,
          source['edges'] = []
      };
      if (target.edges == undefined) {
          target['label'] = d.target,
          target['edges'] = []
      };
      source.edges.push(d);
      target.edges.push(d);
  });
  console.debug('after links')
  var states = b_nodes

  links.forEach(function (d) {
      d.source = b_nodes.filter(function(node){return node.id == d.source;})[0]
      d.target = b_nodes.filter(function(node){return node.id == d.target;})[0]
  });

  // Now start laying things out
  var svg = d3.select("svg");
  var svgGroup = svg.append("g").attr("transform", "translate(5, 5)");

  // `nodes` is center positioned for easy layout later
  var nodes = svgGroup.selectAll("g .node")
      .data(states)
      .enter()
      .append("g")
      .attr("class", "node")
      .attr("id", function (d) {
      return "node-" + d.label
  });

  var edges = svgGroup.selectAll("path .edge")
      .data(links)
      .enter()
      .append("path")
      .attr("class", "edge")
      .attr("marker-end", "url(#arrowhead)");

  // Append rectangles to the nodes. We do this before laying out the text
  // because we want the text above the rectangle.
  var rects = nodes.append("rect");

  // Append text
  var labels = nodes.append("text")
      .attr("text-anchor", "middle")
      .attr("x", 0);

  labels.append("tspan")
      .attr("x", 0)
      .attr("dy", "1em")
      .text(function (d) {
      return d.name;
  });

  // We need width and height for layout.
  labels.each(function (d) {
      var bbox = this.getBBox();
      d.bbox = bbox;
      d.width = bbox.width + 2 * nodePadding;
      d.height = bbox.height + 2 * nodePadding;
  });

  rects.attr("x", function (d) {
      return -(d.bbox.width / 2 + nodePadding);
  })
      .attr("y", function (d) {
      return -(d.bbox.height / 2 + nodePadding);
  })
      .attr("width", function (d) {
      return d.width;
  })
      .attr("height", function (d) {
      return d.height;
  });

  labels.attr("x", function (d) {
      return -d.bbox.width / 2;
  })
      .attr("y", function (d) {
      return -d.bbox.height / 2;
  });

  // Create the layout and get the graph
  dagre.layout()
      .nodeSep(50)
      .edgeSep(10)
      .rankSep(50)
      .nodes(states)
      .edges(links)
      .debugLevel(1)
      .run();

  nodes.attr("transform", function (d) {
      return 'translate(' + d.dagre.x + ',' + d.dagre.y + ')';
  });

  // Ensure that we have at least two points between source and target
  edges.each(function (d) {
      var points = d.dagre.points;
      if (!points.length) {
          var s = e.source.dagre;
          var t = e.target.dagre;
          points.push({
              x: Math.abs(s.x - t.x) / 2,
              y: Math.abs(s.y + t.y) / 2
          });
      }

      if (points.length === 1) {
          points.push({
              x: points[0].x,
              y: points[0].y
          });
      }
  });

  edges
  // Set the id. of the SVG element to have access to it later
  .attr('id', function (e) {
      return e.dagre.id;
  })
      .attr("d", function (e) {
      return spline(e);
  });

  // Resize the SVG element
  var svgBBox = svg.node().getBBox();
  svg.attr("width", svgBBox.width + 10);
  svg.attr("height", svgBBox.height + 10);

  // Drag handlers
 var nodeDrag = d3.behavior.drag()
  // Set the right origin (based on the Dagre layout or the current position)
  .origin(function (d) {
      return d.pos ? {
          x: d.pos.x,
          y: d.pos.y
      } : {
          x: d.dagre.x,
          y: d.dagre.y
      };
  })
      .on('drag', function (d, i) {
      var prevX = d.dagre.x,
          prevY = d.dagre.y;

      // The node must be inside the SVG area
      d.dagre.x = Math.max(d.width / 2, Math.min(svgBBox.width - d.width / 2, d3.event.x));
      d.dagre.y = Math.max(d.height / 2, Math.min(svgBBox.height - d.height / 2, d3.event.y));
      d3.select(this).attr('transform', 'translate(' + d.dagre.x + ',' + d.dagre.y + ')');

      var dx = d.dagre.x - prevX,
          dy = d.dagre.y - prevY;

      // Edges position (inside SVG area)
      d.edges.forEach(function (e) {
          translateEdge(e, dx, dy);
          d3.select('#' + e.dagre.id).attr('d', spline(e));
      });
  });

  var edgeDrag = d3.behavior.drag()
      .on('drag', function (d, i) {
      translateEdge(d, d3.event.dx, d3.event.dy);
      d3.select(this).attr('d', spline(d));
  });
 
  nodes.call(nodeDrag);
  edges.call(edgeDrag);

  refreshBuilds('/jenkinsflow/builds')
}}

