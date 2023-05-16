import { useEffect, useState } from "react";
import styles from "./content.module.scss";
import { db, storage } from "../firebaseConfig";
import { onValue, ref } from "firebase/database";
import {
  getStorage,
  ref as storageRef,
  getDownloadURL,
} from "firebase/storage";

const Content = () => {
  const [temperature, setTemperature] = useState(null);
  const [humidity, setHumidity] = useState(null);
  const [cameraTemperature, setCameraTemperature] = useState(null);
  const [imageUrl, setImageUrl] = useState(null);

  useEffect(() => {
    const dhtSensorRef = ref(db, "dht_sensor");
    const cameraSensorRef = ref(db, "camera_sensor");

    onValue(dhtSensorRef, (snapshot) => {
      const { temperature, humidity } = snapshot.val();
      setTemperature(temperature);
      setHumidity(humidity);
    });

    onValue(cameraSensorRef, (snapshot) => {
      const temperature = snapshot.val().temperature;
      setCameraTemperature(Math.round(temperature));
    });

    // Fetch the image URL from Firebase Storage
    const storageInstance = getStorage();
    const imageRef = storageRef(storageInstance, "image_capture.png");

    const fetchImageUrl = () => {
      getDownloadURL(imageRef)
        .then((url) => {
          setImageUrl(url);
        })
        .catch((error) => {
          console.log("Error fetching image URL:", error);
        });
    };

    // Fetch the initial image URL
    fetchImageUrl();

    // Fetch a new image URL every 500 millisecond
    const interval = setInterval(fetchImageUrl, 100);

    // Clean up the interval when the component is unmounted
    return () => clearInterval(interval);
  }, []);

  return (
    <div className={styles.contentBG}>
      <div className={styles.cameraImage}>
        {imageUrl && <img src={imageUrl} alt="Camera" />}
      </div>
      <div className={styles.sensors}>
        <div className={styles.dayCount}>
          <h1>Day</h1>
          <p>1</p>
        </div>
        <div className={styles.dhtSensor}>
          <h1>DHT11</h1>
          <p>Temperature: {temperature} °C</p>
          <p>Humidity: {humidity} %</p>
        </div>
        <div className={styles.camSensor}>
          <h1>MLX90640</h1>
          <p>Temperature: {cameraTemperature} °C</p>
        </div>

        <div className={styles.fan}>
          <h1>Fan</h1>
          <p>Status: OFF</p>
        </div>

        <div className={styles.motor}>
          <h1>Motor</h1>
          <p>Status: OFF</p>
        </div>
      </div>
    </div>
  );
};

export default Content;
