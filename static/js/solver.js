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
    if (node.kind == 'problem' || node.kind == 'expression') {
      // Graph expression labels arrive as TeX without delimiters.  Add
      // MathJax inline delimiters while still inserting the label as text,
      // so arbitrary input can never become HTML.
      $node.text('\\(' + node.label + '\\)')
    } else {
      $node.text(node.label)
    }
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

  function typeset_results(done) {
    // MathJax 2 Typeset accepts one DOM element per command.  Passing an
    // array makes it process only the first element, which left every graph
    // label as raw TeX even though the explanation rendered correctly.
    MathJax.Hub.Queue(["Typeset", MathJax.Hub, $problem_response[0]])
    MathJax.Hub.Queue(["Typeset", MathJax.Hub, $and_or_graph[0]])
    if (done) MathJax.Hub.Queue(done)
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

        typeset_results()
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
    // Wait until MathJax has replaced every TeX label before opening the
    // browser print dialog.  afterprint keeps print-only styling active for
    // the complete print/PDF operation.
    typeset_results(function() {
      $('body').addClass('printing-graph')
      window.print()
    })
  })

  $(window).on('afterprint', function() {
    $('body').removeClass('printing-graph')
  })
})
