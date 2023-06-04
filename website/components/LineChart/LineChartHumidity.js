import { useEffect, useState, useRef } from "react";
import styles from "./chart.module.scss";
import { Line } from "react-chartjs-2";
import { db } from "../firebaseConfig";
import { get, ref, off, set } from "firebase/database";
import {
  Chart,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

Chart.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const LineChartHumidity = () => {
  const dhtSensorRef = useRef(null);

  const [chartData, setChartData] = useState({
    labels: [],
    datasets: [
      {
        label: "DHT Sensor Humidity",
        data: [],
        borderColor: "rgb(53, 162, 235)",
        backgroundColor: "rgba(53, 162, 235, 0.5)",
      },
    ],
  });

  const getTimestampString = () => {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes().toString().padStart(2, "0");
    const ampm = hours >= 12 ? "PM" : "AM";
    const formattedHours = hours % 12 || 12;
    return `${formattedHours}:${minutes} ${ampm}`;
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const dhtSensorSnapshot = await get(ref(db, `dht_sensor/humidity`));
        const dhtSensorData = dhtSensorSnapshot.val();

        if (dhtSensorData) {
          const dhtSensorHumidity = dhtSensorData;
          setChartData((prevData) => ({
            ...prevData,
            datasets: [
              {
                ...prevData.datasets[0],
                data: [...prevData.datasets[0].data, dhtSensorHumidity],
              },
            ],
            labels: [...prevData.labels, getTimestampString()],
          }));
          const lineChartDHTTempRef = ref(
            db,
            `line_chart_humidity/${getTimestampString()}/dht_humidity`
          );
          set(lineChartDHTTempRef, dhtSensorHumidity);
        }
      } catch (error) {
        console.log("Error fetching data: ", error);
      }
    };

    const fetchPreviousData = async () => {
      try {
        const lineChartSnapshot = await get(ref(db, `line_chart_humidity`));
        const lineChartData = lineChartSnapshot.val();

        if (lineChartData) {
          const labels = Object.keys(lineChartData);
          const dhtSensorData = labels.map(
            (label) => lineChartData[label].dht_humidity
          );

          setChartData({
            labels: labels,
            datasets: [
              {
                ...chartData.datasets[0],
                data: dhtSensorData,
              },
            ],
          });
        }
      } catch (error) {
        console.log("Error fetching previous data: ", error);
      }
    };

    fetchData();
    fetchPreviousData();

    const interval = setInterval(fetchData, 60000);

    return () => {
      clearInterval(interval);
      if (dhtSensorRef.current) off(dhtSensorRef.current);
    };
  }, []);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top",
        labels: {
          color: "white",
        },
      },
      title: {
        display: true,
        text: "Humidity",
        color: "white",
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: "Humidity (%)",
          color: "white",
        },
        ticks: {
          color: "white",
        },
      },
      x: {
        title: {
          display: true,
          text: "Time",
          color: "white",
        },
        ticks: {
          color: "white",
        },
      },
    },
  };

  if (chartData.labels.length === 0) {
    return null;
  }

  return (
    <div className={styles.chartBG}>
      <Line options={options} data={chartData} />
    </div>
  );
};

export default LineChartHumidity;
