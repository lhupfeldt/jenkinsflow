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
              console.error(error.message);
          } else {
              links = json["links"].map(function(s) {
                return { u: s.source, v: s.target, value: { label: '' } };
              });
              nodes = json["nodes"].map(function(s) {
                return { id: s.id, value: { label: s.name } };
              });
              job_urls =json["nodes"].map(function(s) {
                return s.url;
              });
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
        var renderer = new dagreD3.Renderer();
        var oldDrawNodes = renderer.drawNodes();
        renderer.drawNodes(function(graph, root) {
          var svgNodes = oldDrawNodes(graph, root);
          svgNodes.attr("id", function(u) { return "node-" + u; });
          return svgNodes;
        });
        var layout = renderer.run(dagreD3.json.decode(nodes, links), d3.select("svg g"));
        d3.select("svg")
          .attr("width", layout.graph().width + 40)
          .attr("height", layout.graph().height + 40);
    }
}
