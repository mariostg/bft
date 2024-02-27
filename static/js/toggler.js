function toggle_comments() {
    const toggling = document.querySelectorAll(".cantoggle");
    toggling.forEach((item) => {
        item.classList.toggle("hide");
    });
}

function set_comment_visibility(hidden) {
    const toggling = document.querySelectorAll(".cantoggle");
    toggling.forEach((item) => {
        hidden ? item.classList.add("hide") : item.classList.remove("hide");
    });
}

const text_toggler = document.getElementById("comment-toggler");
if (text_toggler) {
    console.log("Hidden " + JSON.parse(sessionStorage.getItem("comment_hidden")));
    text_toggler.addEventListener("click", (event) => {
        let comment_hidden = !JSON.parse(sessionStorage.getItem("comment_hidden"));
        sessionStorage.setItem("comment_hidden", comment_hidden);
        toggle_comments();
    });
}
addEventListener("load", (event) => {
    comment_hidden = JSON.parse(sessionStorage.getItem("comment_hidden"));
    if (comment_hidden) {
        set_comment_visibility(true);
    }
});
