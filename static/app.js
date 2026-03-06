(function() {
  var restaurants = [];
  var currentTab = "visited";
  var editingId = null;
  var selectedRating = null;
  var tempMarker = null;
  var searchTimeout = null;
  var modalOpen = false;
  var map = L.map("map").setView([37.7749, -122.4194], 13);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution: "&copy; OpenStreetMap contributors &copy; CARTO",
    maxZoom: 19
  }).addTo(map);
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      function(pos) { map.setView([pos.coords.latitude, pos.coords.longitude], 13); },
      function() {}
    );
  }
  map.on("click", function(e) {
    if (!modalOpen) return;
    setFormLocation(e.latlng.lat, e.latlng.lng);
    fetch("https://nominatim.openstreetmap.org/reverse?lat=" + e.latlng.lat + "&lon=" + e.latlng.lng + "&format=json")
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.display_name) {
          document.getElementById("form-address").value = data.display_name;
        }
      });
  });
  var markersLayer = L.layerGroup().addTo(map);
  function makeIcon(status) {
    var color = status === "visited" ? "#e94560" : "#53d8fb";
    var div = document.createElement("div");
    div.setAttribute("style",
      "width:16px;height:16px;" +
      "background:" + color + ";" +
      "border:3px solid white;" +
      "border-radius:50%;" +
      "box-shadow:0 2px 6px rgba(0,0,0,0.4);"
    );
    return L.divIcon({
      className: "",
      html: div.outerHTML,
      iconSize: [16, 16],
      iconAnchor: [8, 8],
      popupAnchor: [0, -12]
    });
  }
  function renderMarkers() {
    markersLayer.clearLayers();
    for (var i = 0; i < restaurants.length; i++) {
      var r = restaurants[i];
      var m = L.marker([r.lat, r.lng], { icon: makeIcon(r.status) });
      var popup = "<b>" + esc(r.name) + "</b>";
      if (r.rating) popup += ' <span style="color:#e94560">' + r.rating + "/10</span>";
      if (r.address) popup += "<br><small>" + esc(r.address) + "</small>";
      if (r.notes) popup += "<br><em>" + esc(r.notes) + "</em>";
      m.bindPopup(popup);
      markersLayer.addLayer(m);
    }
  }
  function switchTab(tab) {
    currentTab = tab;
    var tabs = document.querySelectorAll(".sidebar-tab");
    for (var i = 0; i < tabs.length; i++) {
      if (tabs[i].getAttribute("data-tab") === tab) {
        tabs[i].classList.add("active");
      } else {
        tabs[i].classList.remove("active");
      }
    }
    renderList();
  }
  function renderList() {
    var list = document.getElementById("restaurant-list");
    var filtered = [];
    for (var i = 0; i < restaurants.length; i++) {
      if (restaurants[i].status === currentTab) filtered.push(restaurants[i]);
    }
    if (filtered.length === 0) {
      var msg = currentTab === "visited"
        ? "No restaurants yet! Add places you've been to."
        : "Your wishlist is empty! Add places you want to try.";
      list.innerHTML = '<div class="empty-state">' + msg + "</div>";
      return;
    }
    var html = "";
    for (var i = 0; i < filtered.length; i++) {
      var r = filtered[i];
      html += '<div class="restaurant-card" data-lat="' + r.lat + '" data-lng="' + r.lng + '">';
      html += '<div class="card-header">';
      html += '<span class="card-name">' + esc(r.name) + "</span>";
      if (r.rating) html += '<span class="card-rating">' + r.rating + "/10</span>";
      html += "</div>";
      if (r.address) html += '<div class="card-address">' + esc(r.address) + "</div>";
      if (r.notes) html += '<div class="card-notes">' + esc(r.notes) + "</div>";
      html += '<div class="card-actions">';
      html += '<button class="btn-sm btn-edit" data-edit-id="' + r.id + '">Edit</button>';
      html += '<button class="btn-sm btn-delete" data-delete-id="' + r.id + '">Delete</button>';
      html += "</div>";
      html += "</div>";
    }
    list.innerHTML = html;
  }
  function esc(s) {
    if (!s) return "";
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }
  function flyTo(lat, lng) {
    map.flyTo([lat, lng], 16);
  }
  function openModal(status) {
    editingId = null;
    selectedRating = null;
    modalOpen = true;
    document.getElementById("modal-title").textContent = "Add Restaurant";
    document.getElementById("form-name").value = "";
    document.getElementById("form-address").value = "";
    document.getElementById("form-lat").value = "";
    document.getElementById("form-lng").value = "";
    document.getElementById("form-status").value = status || "visited";
    document.getElementById("form-notes").value = "";
    document.getElementById("search-input").value = "";
    document.getElementById("search-results").innerHTML = "";
    toggleRatingVisibility();
    buildRatingButtons();
    document.getElementById("modal-overlay").classList.add("active");
  }
  function editRestaurant(id) {
    var r = null;
    for (var i = 0; i < restaurants.length; i++) {
      if (restaurants[i].id === id) { r = restaurants[i]; break; }
    }
    if (!r) return;
    editingId = id;
    selectedRating = r.rating;
    modalOpen = true;
    document.getElementById("modal-title").textContent = "Edit Restaurant";
    document.getElementById("form-name").value = r.name;
    document.getElementById("form-address").value = r.address || "";
    document.getElementById("form-lat").value = r.lat;
    document.getElementById("form-lng").value = r.lng;
    document.getElementById("form-status").value = r.status;
    document.getElementById("form-notes").value = r.notes || "";
    document.getElementById("search-input").value = "";
    document.getElementById("search-results").innerHTML = "";
    toggleRatingVisibility();
    buildRatingButtons();
    document.getElementById("modal-overlay").classList.add("active");
  }
  function closeModal() {
    modalOpen = false;
    document.getElementById("modal-overlay").classList.remove("active");
    if (tempMarker) { map.removeLayer(tempMarker); tempMarker = null; }
  }
  function toggleRatingVisibility() {
    var status = document.getElementById("form-status").value;
    document.getElementById("rating-group").style.display = status === "visited" ? "" : "none";
  }
  function buildRatingButtons() {
    var container = document.getElementById("rating-buttons");
    container.innerHTML = "";
    for (var i = 1; i <= 10; i++) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "rating-btn" + (selectedRating === i ? " selected" : "");
      btn.textContent = i;
      btn.setAttribute("data-rating", i);
      container.appendChild(btn);
    }
  }
  function setFormLocation(lat, lng) {
    document.getElementById("form-lat").value = lat;
    document.getElementById("form-lng").value = lng;
    if (tempMarker) map.removeLayer(tempMarker);
    tempMarker = L.marker([lat, lng]).addTo(map);
  }
  function debounceSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(doSearch, 400);
  }
  function doSearch() {
    var q = document.getElementById("search-input").value.trim();
    if (q.length < 3) {
      document.getElementById("search-results").innerHTML = "";
      return;
    }
    var bounds = map.getBounds();
    var viewbox = bounds.getWest() + "," + bounds.getNorth() + "," + bounds.getEast() + "," + bounds.getSouth();
    fetch("https://nominatim.openstreetmap.org/search?q=" + encodeURIComponent(q) + "&format=json&limit=5&viewbox=" + viewbox + "&bounded=0&addressdetails=1")
      .then(function(r) { return r.json(); })
      .then(function(results) {
        var container = document.getElementById("search-results");
        if (results.length === 0) {
          container.innerHTML = '<div class="search-result" style="color:#888">No results found</div>';
          return;
        }
        var html = "";
        for (var i = 0; i < results.length; i++) {
          var r = results[i];
          html += '<div class="search-result" data-sr-lat="' + r.lat + '" data-sr-lon="' + r.lon + '" data-sr-name="' + esc(r.display_name) + '">';
          html += '<div class="search-result-name">' + esc(r.display_name.split(",")[0]) + "</div>";
          html += '<div class="search-result-addr">' + esc(r.display_name) + "</div>";
          html += "</div>";
        }
        container.innerHTML = html;
      });
  }
  function selectSearchResult(lat, lng, displayName) {
    setFormLocation(lat, lng);
    document.getElementById("form-address").value = displayName;
    document.getElementById("search-results").innerHTML = "";
    document.getElementById("search-input").value = "";
    if (!document.getElementById("form-name").value) {
      document.getElementById("form-name").value = displayName.split(",")[0];
    }
    map.flyTo([lat, lng], 16);
  }
  function loadRestaurants() {
    fetch("/api/restaurants")
      .then(function(res) { return res.json(); })
      .then(function(data) {
        restaurants = data;
        renderMarkers();
        renderList();
      });
  }
  function saveRestaurant() {
    var name = document.getElementById("form-name").value.trim();
    var lat = parseFloat(document.getElementById("form-lat").value);
    var lng = parseFloat(document.getElementById("form-lng").value);
    if (!name) { alert("Please enter a restaurant name."); return; }
    if (isNaN(lat) || isNaN(lng)) { alert("Please search for a location or click on the map."); return; }
    var data = {
      name: name,
      address: document.getElementById("form-address").value,
      lat: lat,
      lng: lng,
      status: document.getElementById("form-status").value,
      rating: document.getElementById("form-status").value === "visited" ? selectedRating : null,
      notes: document.getElementById("form-notes").value
    };
    var url = editingId ? "/api/restaurants/" + editingId : "/api/restaurants";
    var method = editingId ? "PUT" : "POST";
    fetch(url, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    }).then(function() {
      closeModal();
      loadRestaurants();
    });
  }
  function deleteRestaurant(id) {
    if (!confirm("Delete this restaurant?")) return;
    fetch("/api/restaurants/" + id, { method: "DELETE" })
      .then(function() { loadRestaurants(); });
  }
  // --- Event listeners (no inline handlers) ---
  document.getElementById("btn-add-visited").addEventListener("click", function() {
    openModal("visited");
  });
  document.getElementById("btn-add-wishlist").addEventListener("click", function() {
    openModal("wishlist");
  });
  document.getElementById("tab-visited").addEventListener("click", function() {
    switchTab("visited");
  });
  document.getElementById("tab-wishlist").addEventListener("click", function() {
    switchTab("wishlist");
  });
  document.getElementById("search-input").addEventListener("input", debounceSearch);
  document.getElementById("form-status").addEventListener("change", toggleRatingVisibility);
  document.getElementById("btn-cancel").addEventListener("click", closeModal);
  document.getElementById("btn-save").addEventListener("click", saveRestaurant);
  // Event delegation for dynamic content
  document.getElementById("restaurant-list").addEventListener("click", function(e) {
    var editBtn = e.target.closest("[data-edit-id]");
    if (editBtn) {
      e.stopPropagation();
      editRestaurant(parseInt(editBtn.getAttribute("data-edit-id")));
      return;
    }
    var deleteBtn = e.target.closest("[data-delete-id]");
    if (deleteBtn) {
      e.stopPropagation();
      deleteRestaurant(parseInt(deleteBtn.getAttribute("data-delete-id")));
      return;
    }
    var card = e.target.closest(".restaurant-card");
    if (card) {
      flyTo(parseFloat(card.getAttribute("data-lat")), parseFloat(card.getAttribute("data-lng")));
    }
  });
  document.getElementById("search-results").addEventListener("click", function(e) {
    var item = e.target.closest(".search-result");
    if (item && item.getAttribute("data-sr-lat")) {
      selectSearchResult(
        parseFloat(item.getAttribute("data-sr-lat")),
        parseFloat(item.getAttribute("data-sr-lon")),
        item.getAttribute("data-sr-name")
      );
    }
  });
  document.getElementById("rating-buttons").addEventListener("click", function(e) {
    var btn = e.target.closest("[data-rating]");
    if (btn) {
      var val = parseInt(btn.getAttribute("data-rating"));
      selectedRating = selectedRating === val ? null : val;
      buildRatingButtons();
    }
  });
  // Init
  loadRestaurants();
})();
