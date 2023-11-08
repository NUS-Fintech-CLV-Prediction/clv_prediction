document.getElementById("helpBtn").addEventListener("click", function () {
  window.location.href = "help";
});
document.getElementById("feedbackBtn").addEventListener("click", function () {
  alert("Todo: link to feedback form");
});

const dropzone = document.getElementById("dropzone");
const dropzoneDescription = document.getElementById("dropzone-description");
const loader = document.getElementById("loader");
const loaderContainer = document.querySelector(".loader-container");

dropzone.addEventListener("click", function () {
  let fileInput = document.createElement("input");
  fileInput.type = "file";

  fileInput.addEventListener("change", function () {
    if (this.files.length) {
      uploadFile(this.files[0]);
    }
  });

  fileInput.click();
});

dropzone.addEventListener("dragover", function (e) {
  e.preventDefault();
  this.style.backgroundColor = "#e9e9e9";
});

dropzone.addEventListener("dragleave", function (e) {
  this.style.backgroundColor = "#44de33";
});

dropzone.addEventListener("drop", function (e) {
  e.preventDefault();
  this.style.backgroundColor = "#44de33";

  const files = e.dataTransfer.files;
  if (files.length) {
    uploadFile(files[0]);
  }
});

function startLoading() {
  loaderContainer.style.display = "block";

  // Simulate loading by increasing the width of the loader bar over time
  let width = 0;
  const interval = setInterval(function () {
    if (width >= 100) {
      clearInterval(interval);
      loaderContainer.style.display = "none";
    } else {
      width++;
      loader.style.width = width + "%";
    }
  }, 300); // Adjust the interval duration to control the loading speed
}

function uploadFile(file) {
  const months = document.getElementById("monthsInput").value;
  if (!months) {
    alert("Please enter the number of months.");
    return;
  }
  startLoading();
  dropzoneDescription.innerHTML = `<b>Uploading </b>"${file.name}"<b>...</b>`;

  const formData = new FormData();
  formData.append("file", file);
  formData.append("months", months);

  fetch("/upload", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      loaderContainer.style.display = "none";
      dropzoneDescription.innerHTML = `<b>Drag & drop your CSV file here </b><br/> or click to select a file`;
      if (response.ok) {
        alert("File uploaded successfully!");
        window.location.href = window.location.href + "download";
      } else {
        alert("Error uploading the file.");
      }
    })
    .catch((error) => {
      console.error("There was an error uploading your file:", error);
    });
}
