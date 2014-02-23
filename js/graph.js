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
  var job_urls = []

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

function refreshBuilds() {
    var f = function() {
        for(var i = job_urls.length - 1; i >= 0; i--) {
            console.debug('refresh job=' + job_urls[i])
            var url = '/jenkinsflow/build/' + job_urls[i]
            new Ajax.Request(url, {
                onSuccess: function (rsp) {
                    window.setTimeout(f, 2000);
                }
            })
            console.debug('after ajax')
        }
    }
    console.debug('Before timeout')
    window.setTimeout(f, 2000);
}

Queue = {
    _1: [],
    _2: 0,

    indexOf: function(needle) {
        return this._1.indexOf(needle);
    },

    getLength: function() {
        return (this._1.length - this._2);
    },

    isEmpty: function() {
        return (this._1.length==0);
    },

    push: function(_3) {
        this._1.push(_3);
    },

    pop: function() {
        if (this._1.length == 0) {
            return undefined;
        }
        var _4 = this._1[this._2];
        if (++this._2*2 >= this._1.length) {
            this._1 = this._1.slice(this._2);
            this._2=0;
        }
        return _4;
    },

    peek: function() {
        return (this._1.length>0?this._1[this._2]:undefined);
    }
};

AjaxQueue = {
    urls: Queue,

    add: function(url) {
        console.debug('Queue.add called')
        if (!this.urls.indexOf(url) > -1) {
            this.urls.push(url);
            this.poll();
        } else {
            console.debug('Url '+ url +' exists, skipping')
        }
    },

    exists: function(needle) {
        if (typeof Array.prototype.indexOf === 'function') {
            indexOf = Array.prototype.indexOf;
        } else {
            indexOf = function(needle) {
                var i = -1, index = -1;

                for(i = 0; i < this.urls.length; i++) {
                    if(this.urls[i] === needle) {
                        index = i;
                        break;
                    }
                }

                return index;
            };
        }

        console.debug('In exists, needle pos is '+indexOf.call(this.urls, needle))
        return (indexOf.call(this.urls, needle) > -1);
    },

    resetBoxes: function() {
        nodes.forEach(function (n) {
            d3.select("#node-" + n.label + ">rect").style("fill", "#fff");
        })
    },

    updateAjaxQueue: function(items) {
        items.forEach(function (j) {
            var selected = d3.select("#node-" + j.task.name + ">rect");
            selected.style("fill", "#CADFE7");
            window.setTimeout(function f() {
                AjaxQueue.add('/jenkinsflow/build/' + j.task.name)
            }, 2000);
        })
    },

    updateBuild: function(buildJson) {
        console.debug('updateBuild')
        var selected = d3.select("#node-" + buildJson.name + ">rect");
        if (buildJson.lastBuild.number != buildJson.lastCompletedBuild.number) {
            console.debug('lbn != lcbn')
            selected.style("fill", "green");
            window.setTimeout(function f() {
                AjaxQueue.add('/jenkinsflow/build/' + buildJson.name)
            }, 2000);
        } else {
            console.debug('lbn == lcbn')
            selected.style("fill", "#fff");
        }
    },

    poll: function() {
        console.debug('AjaxQueue.poll called')
        if (!this.urls.isEmpty()) {
            url = this.urls.pop();
            console.debug('AjaxQueue.poll url=' + url)
            new Ajax.Request(url, {
                onSuccess: function(rsp) {
                    json = rsp.responseJSON;

                    if (json.items == undefined) {
                        AjaxQueue.updateBuild(json);
                    } else {
                        AjaxQueue.updateAjaxQueue(json.items);
                    }
                    window.setTimeout(function f() {
                        AjaxQueue.add('/jenkinsflow/builds');
                    }, 2000);
                }
            });
        } else {
            console.debug('AjaxQueue is empty')
        }
    }
}

function refreshQueue(url) {
    var f = function() {
        new Ajax.Request(url, {
            onSuccess: function(rsp) {
                console.debug(rsp.responseJSON);
                jsn = rsp.responseJSON;
                console.debug(jsn);
                nodes.forEach(function (n) {
                    d3.select("#node-" + n.label + ">rect").style("fill", "#fff");
                })
                console.debug("Before update in json");
                refreshBuilds();
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

  AjaxQueue.add('/jenkinsflow/builds');
  // refreshQueue('/jenkinsflow/builds');
  // refreshBuilds();
}}

