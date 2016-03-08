/* javascript */
String.prototype.format = function() {
    var formatted = this;
    for (var arg in arguments) {
        formatted = formatted.replace("{" + arg + "}", arguments[arg]);
    }
    return formatted;
};

$(document).on("click", "input.click-select", function(e) {
    $(e.target).select();
});