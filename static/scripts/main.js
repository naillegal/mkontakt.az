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

document.addEventListener("DOMContentLoaded", () => {
  const searchBar = document.getElementById("header-search");
  const searchInput = searchBar?.querySelector("input");
  const openBtns = document.querySelectorAll(".search-toggle");
  const closeBtn = searchBar?.querySelector(".close-search");

  openBtns.forEach((btn) =>
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      searchBar.classList.add("active");
      searchInput?.focus();
    })
  );

  function closeSearch() {
    searchBar.classList.remove("active");
    searchInput.value = "";
  }
  closeBtn?.addEventListener("click", closeSearch);

  document.addEventListener("click", (e) => {
    if (
      searchBar.classList.contains("active") &&
      !searchBar.contains(e.target)
    ) {
      closeSearch();
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeSearch();
  });
});

var bannerSwiper = new Swiper(".bannerSwiper", {
  slidesPerView: 1,
  spaceBetween: 0,
  loop: true,
  navigation: {
    nextEl: ".bannerSwiper .swiper-button-next",
    prevEl: ".bannerSwiper .swiper-button-prev",
  },
  pagination: {
    el: ".bannerSwiper .swiper-pagination",
    clickable: true,
  },
  autoplay: {
    delay: 5000,
    disableOnInteraction: false,
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

  document.querySelectorAll("input[name='category']").forEach((categoryCb) => {
    categoryCb.addEventListener("change", () => {
      const li = categoryCb.closest("li");
      if (!li) return;
      li.querySelectorAll("input[name='subcategory']").forEach((subCb) => {
        subCb.checked = categoryCb.checked;
      });
    });
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

      document
        .querySelectorAll("input[name='brand']:checked")
        .forEach((cb) => url.searchParams.append("brand", cb.value));

      document
        .querySelectorAll("input[name='category']:checked")
        .forEach((cb) => url.searchParams.append("category", cb.value));

      document
        .querySelectorAll("input[name='subcategory']:checked")
        .forEach((cb) => url.searchParams.append("subcategory", cb.value));

      document
        .querySelectorAll("input[name^='attr_']:checked")
        .forEach((cb) => url.searchParams.append(cb.name, cb.value));

      const min = document.querySelector("input[name='min_price']");
      const max = document.querySelector("input[name='max_price']");
      if (min?.value) url.searchParams.set("min_price", min.value);
      if (max?.value) url.searchParams.set("max_price", max.value);

      url.searchParams.delete("page");
      window.location.href = url.toString();
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener("click", function (e) {
      e.preventDefault();
      document
        .querySelectorAll(
          "input[name='brand'], input[name='category'], input[name^='attr_']"
        )
        .forEach((cb) => (cb.checked = false));

      document
        .querySelectorAll("input[name='min_price'], input[name='max_price']")
        .forEach((inp) => (inp.value = ""));

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

document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);

  params.getAll("brand").forEach((id) => {
    const cb = document.querySelector(`input[name="brand"][value="${id}"]`);
    if (cb) cb.checked = true;
  });
  params.getAll("category").forEach((id) => {
    const cb = document.querySelector(`input[name="category"][value="${id}"]`);
    if (cb) cb.checked = true;
  });

  params.getAll("subcategory").forEach((id) => {
    const cb = document.querySelector(
      `input[name="subcategory"][value="${id}"]`
    );
    if (cb) cb.checked = true;
  });

  document.querySelectorAll(".filter-by").forEach((group) => {
    const hasChecked =
      group.querySelector('input[name="brand"]:checked') ||
      group.querySelector('input[name="category"]:checked') ||
      group.querySelector('input[name="subcategory"]:checked') ||
      group.querySelector('input[name^="attr_"]:checked');

    if (hasChecked) {
      group.classList.add("active");
    }
  });
});

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

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("#selected-product-info img").forEach((img) => {
    img.style.cursor = "zoom-in";
    img.addEventListener("click", () => {
      const overlay = document.getElementById("lightbox-overlay");
      const lightImg = document.getElementById("lightbox-img");
      lightImg.src = img.src;
      overlay.style.display = "flex";
    });
  });

  document.getElementById("lightbox-close").addEventListener("click", () => {
    document.getElementById("lightbox-overlay").style.display = "none";
  });

  document.getElementById("lightbox-overlay").addEventListener("click", (e) => {
    if (e.target.id === "lightbox-overlay") {
      e.currentTarget.style.display = "none";
    }
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
        window.location.href = `/giriş/?next=${encodeURIComponent(currentUrl)}`;
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
        window.location.href =
          "{% url 'MContact:login' %}?next=" + encodeURIComponent(currentUrl);
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
document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".product-add-to-cart");
  if (!btn) return;

  const productId = btn.dataset.product;
  const csrf = getCookie("csrftoken");

  const cntEl = document.querySelector(".counter .counter-value");
  const quantity = cntEl ? Math.max(1, parseInt(cntEl.textContent, 10)) : 1;

  const variantInput = document.querySelector("input[name='variant']:checked");
  const variantId = variantInput ? parseInt(variantInput.value, 10) : null;

  try {
    const res = await fetch(`/cart/add/${productId}/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrf,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ quantity, variant_id: variantId }),
    });

    const data = await res.json();
    if (!res.ok || data.ok === false) {
      showToast(data.error || "Xəta baş verdi");
      return;
    }

    updateCartCount(data.count);
    showToast("Məhsul səbətə əlavə edildi!");
  } catch (err) {
    console.error(err);
    showToast("Şəbəkə xətası");
  }
});

function updateCartCount(count) {
  document.querySelectorAll(".cart-icon-wrapper").forEach((wrapper) => {
    let badge = wrapper.querySelector(".cart-badge");
    if (count > 0) {
      if (!badge) {
        badge = document.createElement("span");
        badge.className = "cart-badge";
        wrapper.querySelector("a").appendChild(badge);
      }
      badge.textContent = count;
    } else {
      if (badge) badge.remove();
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const langMenus = document.querySelectorAll(".lang-menu");
  langMenus.forEach((menu) => {
    const toggle = menu.querySelector(".lang-toggle");
    if (!toggle) return;

    toggle.addEventListener("click", (e) => {
      e.stopPropagation();
      menu.classList.toggle("active");
    });

    document.addEventListener("click", (e) => {
      if (!menu.contains(e.target)) menu.classList.remove("active");
    });
  });
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
    const codeInput = document.getElementById("discount-code-input");
    const code = codeInput.value.trim();
    if (!code) return;

    const csrftoken = document.querySelector(
      "[name=csrfmiddlewaretoken]"
    )?.value;

    try {
      const res = await fetch("/cart/apply-discount/", {
        method: "POST",
        headers: {
          "X-CSRFToken": csrftoken,
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({ code }),
      });

      const data = await res.json();
      if (res.ok && data.ok) {
        location.reload();
      } else {
        showToast(data.error || "Endirim tətbiq edilərkən xəta baş verdi.");
      }
    } catch (err) {
      console.error(err);
      showToast("Şəbəkə xətası, zəhmət olmasa yenidən cəhd edin.");
    }
  });

// blog detail scripts
document.addEventListener("DOMContentLoaded", function () {
  const mainImg = document.getElementById("main-blog-image");
  const thumbs = document.querySelectorAll(".blog-thumbnails .thumbnail img");

  thumbs.forEach((thumb) => {
    thumb.addEventListener("click", function () {
      mainImg.src = this.dataset.full;
      document
        .querySelectorAll(".blog-thumbnails .thumbnail")
        .forEach((div) => div.classList.remove("active"));
      this.parentElement.classList.add("active");
    });
  });
});


// contact iframe scripts 
document.addEventListener("DOMContentLoaded", function () {
  const tabs = document.querySelectorAll(".branch-tabs li");
  const iframe = document.getElementById("branch-map");

  tabs.forEach((tab) => {
    tab.addEventListener("click", function () {
      tabs.forEach((t) => t.classList.remove("active"));
      this.classList.add("active");
      iframe.src = this.dataset.src;
    });
  });
});
