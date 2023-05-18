import { useEffect, useState } from "react";
import styles from "./content.module.scss";
import { db } from "../firebaseConfig";
import { onValue, ref } from "firebase/database";
import {
  getStorage,
  ref as storageRef,
  getDownloadURL,
} from "firebase/storage";

import { motion } from "framer-motion";

import { BsCalendar4Week, BsFan, BsDeviceSsd } from "react-icons/bs";
import { RiSensorLine } from "react-icons/ri";
import { FaTemperatureLow } from "react-icons/fa";
import { BiCameraHome } from "react-icons/bi";
import { GoLightBulb } from "react-icons/go";
import { HiInformationCircle } from "react-icons/hi";
import { ImSpinner9 } from "react-icons/im";
import { IoBulbSharp } from "react-icons/io5";
import { GiChicken } from "react-icons/gi";

const Content = () => {
  const [temperature, setTemperature] = useState(null);
  const [humidity, setHumidity] = useState(null);
  const [cameraBodyTemp, setBodyTemp] = useState(null);
  const [cameraRoomTemp, setRoomTemp] = useState(null);
  const [imageUrl, setImageUrl] = useState(null);
  const [motorStatus, setMotorStatus] = useState("");
  const [fanStatus, setFanStatus] = useState("");
  const [bulbStatus, setBulbStatus] = useState("");

  useEffect(() => {
    const dhtSensorRef = ref(db, "dht_sensor");
    const cameraSensorRef = ref(db, "camera_sensor");
    const motorStatusRef = ref(db, "motor_status");
    const fanStatusRef = ref(db, "fan_status");
    const bulbStatusRef = ref(db, "bulb_status");

    onValue(dhtSensorRef, (snapshot) => {
      const { temperature, humidity } = snapshot.val();
      setTemperature(temperature);
      setHumidity(humidity);
    });

    onValue(cameraSensorRef, (snapshot) => {
      const { bodyTemp, roomTemp } = snapshot.val();
      setBodyTemp(Math.round(bodyTemp));
      setRoomTemp(Math.round(roomTemp));
    });

    onValue(motorStatusRef, (snapshot) => {
      const motorStatus = snapshot.val().status;
      setMotorStatus(motorStatus);
    });

    onValue(fanStatusRef, (snapshot) => {
      const fanStatus = snapshot.val().status;
      setFanStatus(fanStatus);
    });

    onValue(bulbStatusRef, (snapshot) => {
      const bulbStatus = snapshot.val().status;
      setBulbStatus(bulbStatus);
    });

    // Fetch the image URL from Firebase Storage
    const storageInstance = getStorage();
    const imageRef = storageRef(storageInstance, "image_capture.jpg");

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

    // Fetch a new image URL every 1 second
    const interval = setInterval(fetchImageUrl, 500);

    // Clean up the interval when the component is unmounted
    return () => clearInterval(interval);
  }, []);

  const getStyle1 = () => {
    if (fanStatus === "OFF") return null;
    else return styles.green;
  };

  const getStyle2 = () => {
    if (motorStatus === "OFF") return null;
    else return styles.green;
  };

  const getStyle3 = () => {
    if (bulbStatus === "OFF") return null;
    else return styles.green;
  };

  const iconStyle = () => {
    if (bulbStatus === "OFF") return styles.fanIcon;
    else return styles.fanON;
  };

  return (
    <div className={styles.contentBG}>
      {motorStatus !== "OFF" ? (
        <div className={styles.motorStatus}>
          <div className={styles.infoContainer}>
            <h1>
              <HiInformationCircle className={styles.infoIcon} />
              Information
            </h1>
            <p>Stepper Motor is now {motorStatus}.</p>
          </div>
        </div>
      ) : null}
      <div className={styles.info}>
        <div className={styles.dayCount}>
          <BsCalendar4Week className={styles.dayIcon} />
          <h1>Day</h1>
          <p>
            <span>1</span>
          </p>
        </div>

        <div className={styles.fan}>
          <BsFan className={iconStyle()} />
          <h1>Fan</h1>
          <p>
            Status:{" "}
            <span className={getStyle1()}>{`${
              fanStatus === "OFF" ? "OFF" : "ON"
            }`}</span>
          </p>
        </div>

        <div className={styles.motor}>
          {motorStatus === "OFF" ? (
            <RiSensorLine className={styles.motorIcon} />
          ) : (
            <ImSpinner9 className={styles.motorONIcon} />
          )}

          <h1>Motor</h1>
          <p>
            Status:{" "}
            <span className={getStyle2()}>{`${
              motorStatus === "OFF" ? "OFF" : "ON"
            }`}</span>
          </p>
        </div>

        <div className={styles.bulb}>
          {bulbStatus === "OFF" ? (
            <GoLightBulb className={styles.bulbIcon} />
          ) : (
            <IoBulbSharp className={styles.bulbON} />
          )}
          <h1>Bulb</h1>
          <p>
            Status:{" "}
            <span className={getStyle3()}>
              {`${bulbStatus === "OFF" ? "OFF" : "ON"}`}
            </span>
          </p>
        </div>
      </div>
      <div className={styles.cameraImage}>
        {imageUrl && <img src={imageUrl} alt="Camera" />}
      </div>
      <div className={styles.sensors}>
        <div className={styles.averageTemp}>
          <FaTemperatureLow className={styles.avgTempIcon} />
          <h1>Average Temp.</h1>
          <p>
            <span>{(temperature + cameraRoomTemp) / 2} °C</span>
          </p>
        </div>
        <div className={styles.dhtSensor}>
          <BsDeviceSsd className={styles.dhtIcon} />
          <h1>DHT11</h1>
          <p>
            Temperature: <span>{temperature} °C</span>
          </p>
          <p>
            Humidity: <span>{humidity} %</span>
          </p>
        </div>
        <div className={styles.camSensor}>
          <BiCameraHome className={styles.camIcon} />
          <h1>MLX90640</h1>
          <p>
            Ambient Temp: <span>{cameraRoomTemp} °C</span>
          </p>
          <p>
            Average Body Temp: <span>{cameraBodyTemp} °C</span>
          </p>
        </div>

        <div className={styles.camSensor}>
          <GiChicken className={styles.populationIcon} />
          <h1>Chicks Population</h1>
          <p>
            <span>
              {100 - (100 - (cameraBodyTemp - cameraRoomTemp)) * 0.1} %
            </span>
          </p>
        </div>

        <div className={styles.date}>
          <h1>Start Date</h1>
          <p>5/16/2023</p>
        </div>
      </div>
    </div>
  );
};

export default Content;
