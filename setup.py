
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
'''
def main():
    print("=== Restaurant Tracker Setup ===\n")
    # Install Flask
    print("Installing Flask...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
    print()
    # Create directories
    templates_dir = os.path.join(BASE_DIR, "templates")
    static_dir = os.path.join(BASE_DIR, "static")
    os.makedirs(templates_dir, exist_ok=True)
    os.makedirs(static_dir, exist_ok=True)
    # Write app.py
    app_path = os.path.join(BASE_DIR, "app.py")
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(APP_PY)
    print("Created: " + app_path)
    # Write index.html
    html_path = os.path.join(templates_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(INDEX_HTML)
    print("Created: " + html_path)
    # Write app.js
    js_path = os.path.join(static_dir, "app.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(APP_JS)
    print("Created: " + js_path)
    # Download Leaflet files locally
    print("\nDownloading Leaflet library...")
    try:
        from urllib.request import urlopen
    except ImportError:
        from urllib2 import urlopen
    leaflet_js_url = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    leaflet_css_url = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    for url, filename in [(leaflet_js_url, "leaflet.js"), (leaflet_css_url, "leaflet.css")]:
        dest = os.path.join(static_dir, filename)
        try:
            data = urlopen(url).read()
            with open(dest, "wb") as f:
                f.write(data)
            print("Downloaded: " + filename)
        except Exception as e:
            print("Warning: Could not download " + filename + ": " + str(e))
            print("The app may not work without Leaflet files.")
    print("\n=== Setup complete! ===")
    print("Starting the app...\n")
    print("Open http://localhost:5000 in your browser!\n")
    # Run the app
    subprocess.call([sys.executable, app_path])
if __name__ == "__main__":
    main()
