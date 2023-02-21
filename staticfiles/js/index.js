function toggleinfo(ID) {
    console.log("toggleinfo-" + String(ID))
    var info = document.getElementsByClassName("toggleinfo-" + String(ID));
    Array.from(info).forEach((x) => {
        if (x.style.display === "none") {
            x.style.removeProperty('display');
        } else {
            x.style.display = "none";
        }
    })
}