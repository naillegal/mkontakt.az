// helper to get CSRF token
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    for (let c of document.cookie.split(";")) {
      c = c.trim();
      if (c.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(c.slice(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function showToast(message) {
  const old = document.getElementById("toast-msg");
  if (old) old.remove();

  const toast = document.createElement("div");
  toast.id = "toast-msg";
  toast.textContent = message;
  Object.assign(toast.style, {
    position: "fixed",
    top: "20px",
    right: "20px",
    padding: "10px 20px",
    background: "rgba(20,48,130,0.9)",
    color: "#fff",
    borderRadius: "5px",
    zIndex: 9999,
    fontSize: "14px",
    boxShadow: "0 2px 6px rgba(0,0,0,0.2)",
  });
  document.body.append(toast);
  setTimeout(() => toast.remove(), 2000);
}

// home scripts
var swiper = new Swiper(".mySwiper", {
  slidesPerView: 5,
  spaceBetween: 20,
  loop: true,
  navigation: {
    nextEl: ".swiper-button-next",
    prevEl: ".swiper-button-prev",
  },
  autoplay: {
    delay: 2000,
    disableOnInteraction: false,
  },
  breakpoints: {
    1200: {
      slidesPerView: 8,
    },
    992: {
      slidesPerView: 7,
    },
    768: {
      slidesPerView: 5,
    },
    576: {
      slidesPerView: 4,
    },
    350: {
      slidesPerView: 3,
    },
  },
});

document.addEventListener("DOMContentLoaded", function () {
  const menuIcon = document.querySelector(".responsive-navbar .fa-bars");
  const responsiveMenu = document.querySelector(".responsive-header-container");
  const closeButton = document.querySelector(".close-icon");
  const overlay = document.getElementById("overlay");

  function openMenu() {
    responsiveMenu.style.left = "0";
    overlay.style.display = "block";
    document.body.style.overflow = "hidden";
  }

  function closeMenu() {
    responsiveMenu.style.left = "-100%";
    overlay.style.display = "none";
    document.body.style.overflow = "";
  }

  menuIcon.addEventListener("click", openMenu);
  closeButton.addEventListener("click", closeMenu);
  overlay.addEventListener("click", closeMenu);
});

var adSwiper = new Swiper(".adSwiper", {
  slidesPerView: 1,
  loop: true,
  navigation: {
    nextEl: "#advertisement-slider .swiper-button-next",
    prevEl: "#advertisement-slider .swiper-button-prev",
  },
  autoplay: {
    delay: 5000,
    disableOnInteraction: false,
  },
  pagination: {
    el: "#advertisement-slider .swiper-pagination",
    clickable: true,
  },
});

// products scripts
document.addEventListener("DOMContentLoaded", function () {
  const filterByElements = document.querySelectorAll(".filter-by");

  filterByElements.forEach((filterBy) => {
    const toggleBtn = filterBy.querySelector(".toggle-filter");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        filterBy.classList.toggle("active");
      });
    }
  });

  const regulationContent = document.querySelector(
    ".regulation-products-content"
  );
  const regulationDropdown = document.querySelector(
    ".regulation-products-dropdown"
  );
  if (regulationContent && regulationDropdown) {
    regulationContent.addEventListener("click", function (e) {
      e.stopPropagation();
      regulationDropdown.classList.toggle("active");
    });
  }

  const cheapest = document.querySelector(
    ".regulation-products-dropdown .cheapest"
  );
  const expensive = document.querySelector(
    ".regulation-products-dropdown .expensive"
  );

  function setOrdering(order) {
    const url = new URL(window.location.href);
    url.searchParams.set("ordering", order);
    url.searchParams.delete("page");
    window.location.href = url.toString();
  }

  if (cheapest) {
    cheapest.addEventListener("click", function () {
      setOrdering("price_asc");
    });
  }
  if (expensive) {
    expensive.addEventListener("click", function () {
      setOrdering("price_desc");
    });
  }

  const applyBtn = document.querySelector(".filter-btns .apply-btn");
  const resetBtn = document.querySelector(".filter-btns .reset-btn");

  if (applyBtn) {
    applyBtn.addEventListener("click", function (e) {
      e.preventDefault();
      const url = new URL(window.location.href);
      url.search = "";

      const brandCheckboxes = document.querySelectorAll(
        "input[name='brand']:checked"
      );
      brandCheckboxes.forEach((cb) => {
        url.searchParams.append("brand", cb.value);
      });

      const catCheckboxes = document.querySelectorAll(
        "input[name='category']:checked"
      );
      catCheckboxes.forEach((cb) => {
        url.searchParams.append("category", cb.value);
      });

      const minPriceInput = document.querySelector("input[name='min_price']");
      const maxPriceInput = document.querySelector("input[name='max_price']");
      if (minPriceInput && minPriceInput.value) {
        url.searchParams.set("min_price", minPriceInput.value);
      }
      if (maxPriceInput && maxPriceInput.value) {
        url.searchParams.set("max_price", maxPriceInput.value);
      }

      url.searchParams.delete("page");
      window.location.href = url.toString();
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener("click", function (e) {
      e.preventDefault();
      const brandCheckboxes = document.querySelectorAll("input[name='brand']");
      brandCheckboxes.forEach((cb) => {
        cb.checked = false;
      });

      const catCheckboxes = document.querySelectorAll("input[name='category']");
      catCheckboxes.forEach((cb) => {
        cb.checked = false;
      });

      const minPriceInput = document.querySelector("input[name='min_price']");
      const maxPriceInput = document.querySelector("input[name='max_price']");
      if (minPriceInput) minPriceInput.value = "";
      if (maxPriceInput) maxPriceInput.value = "";

      const url = new URL(window.location.href);
      url.search = "";
      window.location.href = url.toString();
    });
  }
});

document.addEventListener("DOMContentLoaded", function () {
  const minPriceInput = document.querySelector("input[name='min_price']");
  const maxPriceInput = document.querySelector("input[name='max_price']");

  function loadSelections() {
    const filters = JSON.parse(localStorage.getItem("filters")) || {};

    if (filters.brands) {
      filters.brands.forEach((brand) => {
        const checkbox = document.querySelector(
          `input[name='brand'][value='${brand}']`
        );
        if (checkbox) checkbox.checked = true;
      });
    }

    if (filters.categories) {
      filters.categories.forEach((category) => {
        const checkbox = document.querySelector(
          `input[name='category'][value='${category}']`
        );
        if (checkbox) checkbox.checked = true;
      });
    }

    if (filters.min_price) minPriceInput.value = filters.min_price;
    if (filters.max_price) maxPriceInput.value = filters.max_price;
  }

  function saveSelections() {
    const selectedBrands = Array.from(
      document.querySelectorAll("input[name='brand']:checked")
    ).map((cb) => cb.value);
    const selectedCategories = Array.from(
      document.querySelectorAll("input[name='category']:checked")
    ).map((cb) => cb.value);
    const filters = {
      brands: selectedBrands,
      categories: selectedCategories,
      min_price: minPriceInput.value,
      max_price: maxPriceInput.value,
    };
    localStorage.setItem("filters", JSON.stringify(filters));
  }

  function clearSelections() {
    localStorage.removeItem("filters");
  }

  const applyBtn = document.querySelector(".filter-btns .apply-btn");
  if (applyBtn) {
    applyBtn.addEventListener("click", function (e) {
      saveSelections();
    });
  }

  const resetBtn = document.querySelector(".filter-btns .reset-btn");
  if (resetBtn) {
    resetBtn.addEventListener("click", function (e) {
      clearSelections();
    });
  }

  loadSelections();
});

function moveRegulationProducts() {
  const regulation = document.querySelector(".regulation-products");
  const filter = document.querySelector(".filter");
  const originalParent = document.querySelector("#products-container");

  if (window.innerWidth <= 991) {
    const filterAndProducts = document.querySelector(".filter-and-products");
    if (filterAndProducts && regulation && filter) {
      if (regulation.parentNode !== filterAndProducts) {
        filterAndProducts.insertBefore(regulation, filter.nextElementSibling);
      }
    }
  } else {
    if (originalParent && regulation) {
      const filterAndProducts = document.querySelector(".filter-and-products");
      if (filterAndProducts) {
        originalParent.insertBefore(regulation, filterAndProducts);
      }
    }
  }
}
window.addEventListener("resize", moveRegulationProducts);
document.addEventListener("DOMContentLoaded", moveRegulationProducts);

// products detail scripts
var adSwiper = new Swiper(".productDetailSwiper", {
  slidesPerView: 1,
  loop: true,
  navigation: {
    nextEl: "#selected-product-info .swiper-button-next",
    prevEl: "#selected-product-info .swiper-button-prev",
  },
  autoplay: {
    delay: 5000,
    disableOnInteraction: false,
  },
  pagination: {
    el: "#selected-product-info .swiper-pagination",
    clickable: true,
  },
});

document.addEventListener("DOMContentLoaded", function () {
  const slideItems = document.querySelectorAll(
    ".productDetailSwiper .swiper-slide"
  );
  if (slideItems.length <= 1) {
    const btnPrev = document.querySelector(
      "#selected-product-info .swiper-button-prev"
    );
    const btnNext = document.querySelector(
      "#selected-product-info .swiper-button-next"
    );
    const pagination = document.querySelector(
      "#selected-product-info .swiper-pagination"
    );
    if (btnPrev) btnPrev.style.display = "none";
    if (btnNext) btnNext.style.display = "none";
    if (pagination) pagination.style.display = "none";
  }

  const counterValueElem = document.querySelector(".counter .counter-value");
  if (!counterValueElem) return;

  const minusButton = document.querySelector(".counter .counter-btn.minus");
  const plusButton = document.querySelector(".counter .counter-btn.plus");

  minusButton.addEventListener("click", function () {
    let currentValue = parseInt(counterValueElem.textContent, 10);
    if (currentValue > 1) {
      counterValueElem.textContent = currentValue - 1;
    }
  });

  plusButton.addEventListener("click", function () {
    let currentValue = parseInt(counterValueElem.textContent, 10);
    counterValueElem.textContent = currentValue + 1;
  });
});

// form scripts
const passwordIcons = document.querySelectorAll(".password-input i");

passwordIcons.forEach((icon) => {
  icon.addEventListener("click", () => {
    const input = icon.parentElement.querySelector("input");

    if (input.type === "password") {
      input.type = "text";
      icon.classList.remove("fa-eye");
      icon.classList.add("fa-eye-slash");
    } else {
      input.type = "password";
      icon.classList.remove("fa-eye-slash");
      icon.classList.add("fa-eye");
    }
  });
});

const otpInputs = document.querySelectorAll(".otp-container input");

otpInputs.forEach((input, index) => {
  input.addEventListener("input", () => {
    if (
      input.value.length === input.maxLength &&
      index < otpInputs.length - 1
    ) {
      otpInputs[index + 1].focus();
    }
  });
});

document.addEventListener("DOMContentLoaded", function () {
  const inputContainers = document.querySelectorAll(".input-container");

  inputContainers.forEach((container) => {
    const input = container.querySelector("input");
    const icon = container.querySelector("i");

    if (!input || !icon) return;

    icon.addEventListener("click", (e) => {
      e.stopPropagation();
      input.readOnly = false;
      input.focus();
    });

    document.addEventListener("click", (evt) => {
      if (!container.contains(evt.target)) {
        input.readOnly = true;
      }
    });
  });
});

// layout dropdown menu scripts
document.addEventListener("DOMContentLoaded", () => {
  const userMenus = document.querySelectorAll(".user-menu");

  if (!userMenus.length) return;

  userMenus.forEach((menu) => {
    const toggle = menu.querySelector(".user-toggle");
    if (!toggle) return;

    const dropdown = menu.querySelector(".user-dropdown-menu");

    const closeMenu = (e) => {
      if (!menu.contains(e.target)) {
        menu.classList.remove("active");
        document.removeEventListener("click", closeMenu);
      }
    };

    toggle.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();

      const isAuthenticated = toggle.dataset.authenticated === "1";

      if (!isAuthenticated) {
        const currentUrl = window.location.pathname + window.location.search;
        window.location.href = `/login/?next=${encodeURIComponent(currentUrl)}`;
        return;
      }

      menu.classList.toggle("active");

      if (menu.classList.contains("active")) {
        document.addEventListener("click", closeMenu);
      }
    });
  });
});

// wishlist toggle
document.addEventListener("DOMContentLoaded", function () {
  document.body.addEventListener("click", async function (e) {
    const btn = e.target.closest(".product-add-to-favourites");
    if (!btn) return;

    const productId = btn.dataset.product;
    if (!productId) return;

    const csrftoken = document.querySelector(
      "[name=csrfmiddlewaretoken]"
    )?.value;

    try {
      const res = await fetch(`/wishlist/toggle/${productId}/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrftoken,
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      if (res.status === 403) {
        window.location.href = "{% url 'MContact:login' %}?next=" + encodeURIComponent(currentUrl);
        return;
      }

      const json = await res.json();
      if (json.in_wishlist) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    } catch (err) {
      console.error(err);
    }
  });
});

// ============ ADD TO CART ==================
function getCookie(name) {
  let v = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
  return v ? v.pop() : "";
}

document.body.addEventListener("click", async (e) => {
  const addBtn = e.target.closest(".product-add-to-cart");
  if (!addBtn) return;

  const productId = addBtn.dataset.product;
  const csrftoken =
    getCookie("csrftoken") ||
    document.querySelector('meta[name="csrf-token"]').getAttribute("content");

  const res = await fetch(`/cart/add/${productId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrftoken,
      "X-Requested-With": "XMLHttpRequest",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({}),
  });

  const json = await res.json();
  showToast("Məhsul səbətə əlavə edildi!");
});

// ============ CART ACTIONS =================
document.addEventListener("click", async (e) => {
  const target = e.target;

  // PRODUCT COUNT
  if (target.closest(".counter-btn")) {
    const btn = target.closest(".counter-btn");
    const action = btn.dataset.action;
    const itemDiv = btn.closest(".cart-item");
    await updateCart({ action: action, item_id: itemDiv.dataset.id });
  }

  // DELETE 1 ITEM
  if (target.closest(".cart-product-delete")) {
    const itemDiv = target.closest(".cart-item");
    await updateCart({ action: "delete_one", item_id: itemDiv.dataset.id });
  }

  // DELETE SELECTED ITEMS
  if (target.closest(".delete-selected")) {
    const ids = [...document.querySelectorAll(".select-one:checked")].map(
      (chk) => chk.closest(".cart-item").dataset.id
    );
    await updateCart({ action: "delete_selected", ids });
  }

  // SELECT ALL
  if (target.closest(".select-all")) {
    document
      .querySelectorAll(".select-one")
      .forEach((chk) => (chk.checked = true));
  }
});

// helper
async function updateCart(payload) {
  const csrftoken = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
  await fetch("/cart/update/", {
    method: "POST",
    headers: { "X-CSRFToken": csrftoken, "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(() => location.reload());
}

// ============ DISCOUNT CODE ===================
document
  .getElementById("apply-discount")
  ?.addEventListener("click", async () => {
    const code = document.getElementById("discount-code-input").value.trim();
    if (!code) return;
    const csrftoken = document.querySelector(
      "[name=csrfmiddlewaretoken]"
    )?.value;
    const res = await fetch("/cart/apply-discount/", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({ code }),
    });
    if (res.ok) {
      location.reload();
    } else {
      showToast("Kod tapılmadı");
    }
  });

// ============ PRODUCT-DETAIL ADD TO CART ==================
document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".add-to-cart-btn__button");
  if (!btn) return;

  const productId = btn.dataset.product;
  const counterEl = document.querySelector(".counter .counter-value");
  const quantity = counterEl
    ? Math.max(1, parseInt(counterEl.textContent, 10) || 1)
    : 1;

  const csrftoken = getCookie("csrftoken");

  try {
    const res = await fetch(`/cart/add/${productId}/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify({ quantity }),
    });
    const json = await res.json();
    if (res.ok) {
      showToast("Məhsul səbətə əlavə edildi!");
    } else {
      showToast(json.error || "Xəta baş verdi");
    }
  } catch (err) {
    console.error(err);
    showToast("Xəta baş verdi");
  }
});
