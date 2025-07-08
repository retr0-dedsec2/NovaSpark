// Menu latéral
function openMenu() {
  document.getElementById('sideMenu').style.width = '250px';
}
function closeMenu() {
  document.getElementById('sideMenu').style.width = '0';
}

// Mise en surbrillance du lien actif
document.addEventListener('DOMContentLoaded', () => {
  const links = document.querySelectorAll('#sideMenu a');
  const current = window.location.pathname;
  links.forEach(link => {
    if (current.endsWith(link.getAttribute('href'))) {
      link.classList.add('active');
    }
  });

  // Affichage des favoris sur index.html
  const container = document.getElementById('favoritesContainer');
  if (container) {
    let favs = JSON.parse(localStorage.getItem('favorites') || '[]');
    if (favs.length === 0) {
      container.innerHTML = "<p>Aucun favori enregistré.</p>";
    } else {
      favs.forEach(file => {
        const ext = file.split('.').pop().toLowerCase();
        const div = document.createElement('div');
        div.className = 'playlist-item';
        div.innerHTML = `
          ${ext === 'mp4'
            ? '<span class="media-icon">🎬</span>'
            : '<span class="media-icon">🎵</span>'
          }
          <h3>${file}</h3>
          <audio controls src="/assets/${file}"></audio>
        `;
        container.appendChild(div);
      });
    }
  }
});

function addFavorite(filename) {
  const user = localStorage.getItem("currentUser");
  if (!user) {
    alert("Non connecté !");
    return;
  }
  const key = `favorites_${user}`;
  let favs = JSON.parse(localStorage.getItem(key) || '[]');
  if (!favs.includes(filename)) {
    favs.push(filename);
    localStorage.setItem(key, JSON.stringify(favs));
    alert("Ajouté aux favoris !");
  } else {
    alert("Déjà dans les favoris.");
  }
}
