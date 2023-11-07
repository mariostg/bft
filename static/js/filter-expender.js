const tg = document.getElementById("filter-form");
const expender = document.getElementById("expender");
const expender_width = -tg.offsetWidth + 10 + "px";
tg.style.marginLeft = expender_width;
function asidetoggle(state) {
    let tg = document.getElementById("filter-form").style.marginLeft;
    console.log(tg);
    if (tg == expender_width) {
        console.log("closed, need to opwn");
        document.getElementById("filter-form").style.marginLeft = "0";
    } else {
        console.log("open, beed to clise");
        document.getElementById("filter-form").style.marginLeft = expender_width;
    }
}

expender.addEventListener("mouseover", (event) => {
    asidetoggle();
});
