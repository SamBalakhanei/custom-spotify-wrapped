fetch('../static/js/particles-config.json')
  .then(response => response.json())
  .then(config => {
    particlesJS('particles-js', config);  // Corrected typo here
  })
  .catch(error => {
    console.error("Error loading particles config:", error); // Fixed quote in the error message
  });
