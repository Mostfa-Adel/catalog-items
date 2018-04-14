// to make list icon open and close nav
document.getElementById('toggle-nav').addEventListener('click', function() {
    nav = document.getElementById('nav');
    nav_is_open = window.getComputedStyle(nav, null).getPropertyValue('position') == 'relative'
    classes = document.getElementById('nav').className;
    if (nav_is_open) {
        document.getElementById('nav').className =
            classes.replace('open', '').trim() + " close";
    } else {
        document.getElementById('nav').className =
            classes.replace('close', '').trim() + " open";
    }
});