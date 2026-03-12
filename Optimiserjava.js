

function addToBasket(product) {
    let basket = JSON.parse(localStorage.getItem("basket")) || [];
    let existingProduct = basket.find(item => item.id === product.id);

    if (existingProduct) {
        basket = basket.filter(item => item.id !== product.id);
    } else {
        basket.push(product);
    }

    localStorage.setItem("basket", JSON.stringify(basket));
    updateBasketCount();
}

function updateBasketCount() {
    let basket = JSON.parse(localStorage.getItem("basket")) || [];
    document.getElementById("basket-count").textContent = basket.length;
}

function Baskettotalcost() {
    let basket = JSON.parse(localStorage.getItem("basket")) || [];
    let totalCost = basket.reduce((total, product) => total + product.price, 0);
    document.getElementById("total-cost").textContent = totalCost.toFixed(2);
}

function Baskettotalcarbon() {
    let basket = JSON.parse(localStorage.getItem("basket")) || [];
    let totalCarbon = basket.reduce((total, product) => total + product.co2, 0);
    document.getElementById("total-carbon").textContent = totalCarbon;
}

function OptimisedBaskettotalcost(optimisedBasket) {
    let totalCost = optimisedBasket.reduce((total, product) => total + product.price, 0);
    document.getElementById("optimised-total-cost").textContent = totalCost.toFixed(2);
}

function OptimisedBaskettotalcarbon(optimisedBasket) {
    let totalCarbon = optimisedBasket.reduce((total, product) => total + product.co2, 0);
    document.getElementById("optimised-total-carbon").textContent = totalCarbon;
}

function emptyBasket() {
    localStorage.setItem("basket", JSON.stringify([]));
    updateBasketCount();
    document.querySelectorAll('.selected').forEach(el => el.classList.remove('selected'));
    console.log("Basket emptied");
}

function selectProduct(element, product) {
    let basket = JSON.parse(localStorage.getItem("basket")) || [];
    let category = product.id.substring(0, 2);
    let existingProduct = basket.find(item => item.id === product.id);

    if (existingProduct) {
        basket = basket.filter(item => item.id !== product.id);
        element.classList.remove('selected');
    } else {
        if (category) {
            basket = basket.filter(item => !item.id.startsWith(category));
            document.querySelectorAll(`[data-category="${category}"]`).forEach(el => el.classList.remove('selected'));
        }
        basket.push(product);
        element.classList.add('selected');
    }

    localStorage.setItem("basket", JSON.stringify(basket));
    updateBasketCount();
    console.log("Current basket:", basket);
}

// Initialize selected state on page load
document.addEventListener('DOMContentLoaded', function() {
    let basket = JSON.parse(localStorage.getItem("basket")) || [];
    basket.forEach(item => {
        let element = document.querySelector(`[onclick*="${item.id}"]`);
        if (element) {
            element.classList.add('selected');
        }
    });
    updateBasketCount();
    Baskettotalcarbon();
});



function loadBasket() {
    let basket = JSON.parse(localStorage.getItem("basket")) || [];
    let basketContainer = document.getElementById("basket-container");
    basketContainer.innerHTML="";
    basket.forEach(product => {
        let productElement = document.createElement("div");
        productElement.classList.add("basket-item");
        productElement.innerHTML = `
        

            <img src="${product.img}" alt="${product.name}">
            <p>${product.name}</p>
            <p>&#163;${product.price}</p>
            <p>${product.co2} kg of CO2</p>


        `;
        basketContainer.appendChild(productElement);
    });

    Baskettotalcost();

}

async function runOptimisation() {

    let basket = JSON.parse(localStorage.getItem("basket")) || [];

    let response = await fetch("http://localhost:5000/optimise", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(basket)
    });

    let optimisedBasket = await response.json();

    displayOptimisedBasket(optimisedBasket);

}

function getProductImg(product) {
    // If the server returned an img field, use it directly
    if (product.img) return product.img;
    // Otherwise derive it from the product id (e.g. "WM1" -> "WM1.png")
    return product.id + ".png";
}

function displayOptimisedBasket(optimisedBasket) {
    let basketContainer = document.getElementById("optimised-basket-container");
    optimisedBasket.forEach(product => {
        let productElement = document.createElement("div");
        productElement.classList.add("optimised-basket-item");
        productElement.innerHTML = `
            <div>
                <img src="${getProductImg(product)}" alt="${product.name}">
                <p>&#163;${product.price}</p>
                <p>${product.co2} kg of CO2</p>
            </div>
        `;
        basketContainer.appendChild(productElement);
        
    });
    OptimisedBaskettotalcost(optimisedBasket);
    OptimisedBaskettotalcarbon(optimisedBasket);
}

