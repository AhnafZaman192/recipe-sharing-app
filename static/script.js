// Function to toggle dark mode with transition effect
function toggleDarkMode() {
  document.body.classList.add("transition");
  document.body.classList.toggle("dark-mode");
  setTimeout(() => document.body.classList.remove("transition"), 300); // Match the CSS transition time

  // Update Quill editor styles based on theme
  const isDarkMode = document.body.classList.contains("dark-mode");
  const quillBackground = isDarkMode ? "#2d2d2d" : "#ffffff";
  const quillTextColor = isDarkMode ? "#f4f4f9" : "#333";

  if (typeof ingredientsQuill !== "undefined") {
    ingredientsQuill.root.style.backgroundColor = quillBackground;
    ingredientsQuill.root.style.color = quillTextColor;
  }
  if (typeof instructionsQuill !== "undefined") {
    instructionsQuill.root.style.backgroundColor = quillBackground;
    instructionsQuill.root.style.color = quillTextColor;
  }
}

// Dark mode toggle
const toggleButton = document.getElementById("dark-mode-toggle");
const currentTheme = localStorage.getItem("theme");

// Load saved theme
if (currentTheme === "dark") {
  document.body.classList.add("dark-mode");
  toggleButton.innerHTML = '<i class="fas fa-sun"></i>'; // Show sun icon for light mode
} else {
  toggleButton.innerHTML = '<i class="fas fa-moon"></i>'; // Show moon icon for dark mode
}

// Toggle dark mode on icon click
toggleButton.addEventListener("click", () => {
  toggleDarkMode();
  let theme = document.body.classList.contains("dark-mode") ? "dark" : "light";
  toggleButton.innerHTML =
    theme === "dark"
      ? '<i class="fas fa-sun"></i>'
      : '<i class="fas fa-moon"></i>';
  localStorage.setItem("theme", theme); // Save user preference
});

// Search icon and input toggle
const searchIcon = document.getElementById("search-icon");
const searchContainer = document.querySelector(".search-container");
const searchInput = document.getElementById("search-input");

// Show search input on icon click
searchIcon.addEventListener("click", (e) => {
  e.stopPropagation();
  searchContainer.classList.add("active");
  searchInput.focus(); // Automatically focus the input
});

// Close search input if clicked outside and input is empty
document.addEventListener("click", (e) => {
  if (!searchContainer.contains(e.target) && searchInput.value === "") {
    searchContainer.classList.remove("active");
  }
});

// Prevent collapse if there's text in the input
searchInput.addEventListener("input", () => {
  if (searchInput.value !== "") {
    searchContainer.classList.add("active");
  }
});

// Ensure form submission for add/edit recipes is working by submitting hidden fields
document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", () => {
    // Ensure Quill content is submitted in form if fields exist
    if (document.getElementById("ingredients-input")) {
      document.getElementById("ingredients-input").value =
        ingredientsQuill.root.innerHTML;
    }
    if (document.getElementById("instructions-input")) {
      document.getElementById("instructions-input").value =
        instructionsQuill.root.innerHTML;
    }
  });
});
