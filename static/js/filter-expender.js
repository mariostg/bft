const ff = document.getElementById("filter-form");
const expender = document.getElementById("expender");
const expender_width = -ff.offsetWidth + 10 + "px";
function asidetoggle(state) {
    let tg = document.getElementById("filter-form").style.marginLeft;
    fheader = document.querySelector("#filter-form form div.form__header");
    console.log(tg);
    if (tg == expender_width) {
        console.log("closed, need to opwn");
        ff.style.marginLeft = "0";
        fheader.style.background = "#a3b09c";
        expender.style.background = "#a3b09c";
        fheader.style.color = "#4b5544";
    } else {
        console.log("open, beed to clise");
        fheader.style.background = "#4b5544";
        expender.style.background = "#4b5544";
        ff.style.marginLeft = expender_width;
    }
}

expender.addEventListener("mouseover", (event) => {
    asidetoggle();
});
