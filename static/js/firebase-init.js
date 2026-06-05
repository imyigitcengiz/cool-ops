import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";

// Firebase configuration from user request
const firebaseConfig = {
  apiKey: "AIzaSyCr7_6NF3_54EhcvAAx0xdFt-MU-gKf7Zw",
  authDomain: "coolops-5a2de.firebaseapp.com",
  projectId: "coolops-5a2de",
  storageBucket: "coolops-5a2de.firebasestorage.app",
  messagingSenderId: "812333634392",
  appId: "1:812333634392:web:78b9c231cac7b8230a4b2d"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
window.firebaseApp = app;

console.log("Firebase client SDK başarıyla başlatıldı.");
