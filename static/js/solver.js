$(function(){
  console.log('script loaded.')

  var $problem_input = $('input[name="problem-input"]')
  var $problem_solve_btn = $('input[name="problem-solve"]')
  var $problem_status = $('.problem-status')
  var $problem_response = $('.problem-response')
  var $and_or_graph = $('.and-or-graph')

  function graph_node(node) {
    var $item = $('<li>')
    var $node = $('<div>').addClass('graph-node').addClass('graph-' + node.kind)
    if (node.status) $node.addClass('graph-' + node.status)
    $node.text(node.label)
    $item.append($node)
    if (node.children && node.children.length) {
      var $children = $('<ul>')
      $.each(node.children, function(_, child) {
        $children.append(graph_node(child))
      })
      $item.append($children)
    }
    return $item
  }

  function render_graph(graph) {
    $and_or_graph.empty()
    $('<ul>').addClass('graph-tree').append(graph_node(graph)).appendTo($and_or_graph)
  }

  function show_status(status) {
    // status can be "solved", "fetching", or "error"
    if (status != "fetching") {
      $problem_status.text(status)
      $problem_input.removeClass()
      $problem_input.addClass("status-" + status)
    }
  }

  function fetch_problem_solution() {
    var val = $problem_input.val()
    show_status("fetching")

    console.log("sending problem to server ", val)
    $.ajax({
      url: '/API/solve',
      // data: {problem: encodeURIComponent("intx^2dx")},
      data: {problem: val},
      success: function(data) {
        console.log('solution received from server.')
        // console.log('data', data)

        show_status("solved")
        $problem_response.empty()
        $problem_response.append(data.html)
        render_graph(data.graph)

        MathJax.Hub.Queue(["Typeset", MathJax.Hub, $problem_response[0]]);
      },
      error: function() {
        console.error('error from request!')
        show_status("error")
      }
    })
  }

  $problem_solve_btn.click(fetch_problem_solution)
  $problem_input.keyup(fetch_problem_solution)

  $problem_solve_btn.click();

  $('.graph-print').click(function() {
    $('body').addClass('printing-graph')
    window.print()
    $('body').removeClass('printing-graph')
  })
})
