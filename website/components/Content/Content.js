import { useEffect, useState } from "react";
import styles from "./content.module.scss";
import { db } from "../firebaseConfig";
import { onValue, ref } from "firebase/database";

const Content = () => {
  const [temperature, setTemperature] = useState(null);
  const [humidity, setHumidity] = useState(null);
  const [cameraTemperature, setCameraTemperature] = useState(null);

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
  }, []);

  return (
    <div className={styles.contentBG}>
      <div className={styles.dhtSensor}>
        <h1>DHT11</h1>
        <p>Temperature: {temperature} °C</p>
        <p>Humidity: {humidity} %</p>
      </div>

      <div className={styles.camSensor}>
        <h1>MLX90640 Camera</h1>
        <p>Temperature: {cameraTemperature} °C</p>
      </div>
    </div>
  );
};

export default Content;
