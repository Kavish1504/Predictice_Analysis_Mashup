document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form");
  const button = document.getElementById("button");
  const btnText = document.getElementById("btn-text");
  const spinner = document.getElementById("spinner");
  spinner.style.display = "none";

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const singer = document.getElementById("singer").value.trim();
    const videos = document.getElementById("videos").value;
    const duration = document.getElementById("duration").value;
    const email = document.getElementById("email").value.trim();

    if (!singer) {
      alert("Please enter singer name.");
      return;
    }
    if (isNaN(videos) || videos < 10) {
      alert("Number of videos must be 10 or more.");
      return;
    }
    if (isNaN(duration) || duration < 20) {
      alert("Duration must be 20 seconds or more.");
      return;
    }
    if (!email) {
      alert("Please enter a valid email address.");
      return;
    }
    button.disabled = true;
    btnText.style.display = "none";
    spinner.style.display = "block";

    async function checkStatus(jobId) {
      const res = await fetch(`/status/${jobId}`);
      const data = await res.json();
      return data.status;
    }
    try {
      const response = await fetch("/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ singer, videos, duration, email }),
      });

      if (!response.ok) {
        throw new Error("Server error");
      }
      const result = await response.json();
      const jobId = result.job_id;
      
      const interval = setInterval(async () => {
        const status = await checkStatus(jobId);
        if (status === "done") {
          clearInterval(interval);
          spinner.style.display = "none";
          btnText.style.display = "inline";
          button.disabled = false;
          alert("Mashup email sent successfully!");
        } else if (status === "error") {
          clearInterval(interval);
          spinner.style.display = "none";
          btnText.style.display = "inline";
          button.disabled = false;
          alert("Error creating mashup. Please try again or check if videos are available for this singer.");
        }
      }, 5000);
    } catch (error) {
      spinner.style.display = "none";
      btnText.style.display = "inline";
      button.disabled = false;
      alert("Something went wrong. Please try again.");
      console.error(error);
    }
  });
});