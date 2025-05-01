/**
 * Pico.css Dark Mode Switcher
 *
 * Adapted from Pico documentation examples
 * @see https://picocss.com/docs/dark-mode
 */

const themeSwitcher = {
    // Config
    _scheme: "auto",
    menuTarget: "details[role='list']", // Adjust if you use dropdowns
    buttonsTarget: "button[data-theme-switcher]",
    buttonAttribute: "data-theme-switcher",
    rootAttribute: "data-theme",
    localStorageKey: "picoPreferredColorScheme",
  
    // Init
    init() {
      this.scheme = this.preferredColorScheme;
      this.initSwitchers(); // Handle clicks on explicit buttons/links
      this.initToggle();    // Handle click on the single toggle button
    },
  
    // Get preferred scheme
    get preferredColorScheme() {
      if (this._scheme !== "auto") {
        return this._scheme;
      }
      return window.localStorage.getItem(this.localStorageKey) ?? "auto";
    },
  
    // Set scheme
    set scheme(scheme) {
      if (scheme == "auto") {
        this.preferredColorScheme == "dark"
          ? (this._scheme = "dark")
          : (this._scheme = "light");
      } else if (scheme == "dark" || scheme == "light") {
        this._scheme = scheme;
      }
      this.applyScheme();
      this.storeScheme();
    },
  
    // Store scheme to local storage
    storeScheme() {
        // Only store 'dark' or 'light', never 'auto'
        let storingScheme = this._scheme;
        if (this.preferredColorScheme === 'auto') { // If user hasn't manually chosen yet
             storingScheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? 'dark' : 'light';
        }
         window.localStorage.setItem(this.localStorageKey, storingScheme);
    },
  
  
    // Apply scheme to <html>
    applyScheme() {
      const R = document.querySelector("html");
      const T = document.getElementById("theme-toggle"); // Get toggle button
  
      if (this._scheme == "dark") {
         R?.setAttribute(this.rootAttribute, "dark");
         if (T) T.textContent = '☀️'; // Sun icon for dark mode
      } else {
         R?.setAttribute(this.rootAttribute, "light");
         if (T) T.textContent = '🌙'; // Moon icon for light mode
      }
  
      // // Update dropdown/menu active states if used (from Pico example)
      // document.querySelectorAll(this.buttonsTarget).forEach((button) => {
      //   const scheme = button.getAttribute(this.buttonAttribute);
      //   button.setAttribute('aria-pressed', `${scheme === this._scheme}`);
      // });
    },
  
  
    // Init Switcher buttons/links in footer
    initSwitchers() {
       const switchers = document.querySelectorAll("a[data-theme-switcher]"); // Target footer links
       switchers.forEach((switcher) => {
        switcher.addEventListener(
          "click",
          (event) => {
            event.preventDefault();
            this.scheme = switcher.getAttribute("data-theme-switcher");
          },
          false
        );
      });
    },
  
    // Init the single Toggle button in nav
    initToggle() {
      const toggleButton = document.getElementById('theme-toggle');
      if (toggleButton) {
          toggleButton.addEventListener('click', () => {
              this.scheme = (this._scheme === 'light') ? 'dark' : 'light';
          }, false);
      }
    }
  
  };
  
  // Init
  themeSwitcher.init();