import { initializeApp } from 'firebase/app'
import { getDatabase } from 'firebase/database'

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyBq68owsBjnpM6KRiFdJm41nd5mSpKBaW0",
    authDomain: "poultry-monitoring-system-1.firebaseapp.com",
    databaseURL: "https://poultry-monitoring-system-1-default-rtdb.asia-southeast1.firebasedatabase.app",
    projectId: "poultry-monitoring-system-1",
    storageBucket: "poultry-monitoring-system-1.appspot.com",
    messagingSenderId: "265095833387",
    appId: "1:265095833387:web:43286dabe51d0c325a476e"
}

// Initialize Firebase
const app = initializeApp(firebaseConfig)

export const db = getDatabase()