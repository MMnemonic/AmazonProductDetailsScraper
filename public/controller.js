$(document).ready(function() {
    //var asin = document.getElementById("asin").value();
    var asin = "B0762JTR7X";
    $.ajax({
        url: "http://127.0.0.1:5000/search",
        type: "get",
        data: {asin:asin},
        cache: false,
        success: function(d) {
            console.log(d);
        }

    });
});
