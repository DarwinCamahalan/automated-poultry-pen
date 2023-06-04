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
    const resetChartData = async () => {
      try {
        const today = new Date().toLocaleDateString();
        const lineChartHumidityRef = ref(db, "line_chart_humidity");
        const lineChartHumiditySnapshot = await get(lineChartHumidityRef);
        const lineChartHumidityData = lineChartHumiditySnapshot.val();

        if (lineChartHumidityData) {
          const chartDates = Object.keys(lineChartHumidityData);
          const outdatedDates = chartDates.filter((date) => date !== today);

          for (const date of outdatedDates) {
            const dateRef = ref(lineChartHumidityRef, date);
            set(dateRef, null);
          }
        }
      } catch (error) {
        console.log("Error resetting chart data: ", error);
      }
    };

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
          const lineChartDHTHumidityRef = ref(
            db,
            `line_chart_humidity/${getTimestampString()}/dht_humidity`
          );
          set(lineChartDHTHumidityRef, dhtSensorHumidity);
        }
      } catch (error) {
        console.log("Error fetching data: ", error);
      }
    };

    const fetchPreviousData = async () => {
      try {
        const lineChartHumiditySnapshot = await get(
          ref(db, `line_chart_humidity`)
        );
        const lineChartHumidityData = lineChartHumiditySnapshot.val();

        if (lineChartHumidityData) {
          const labels = Object.keys(lineChartHumidityData);
          const dhtSensorData = labels.map(
            (label) => lineChartHumidityData[label].dht_humidity
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

    const resetInterval = setInterval(() => {
      const now = new Date();
      const resetTime = new Date(
        now.getFullYear(),
        now.getMonth(),
        now.getDate(),
        8,
        59,
        0
      );

      if (now >= resetTime) {
        resetChartData();
      }
    }, 60000); // Check every minute if reset time has passed

    const fetchInterval = setInterval(() => {
      const now = new Date();
      const fetchTime = new Date(
        now.getFullYear(),
        now.getMonth(),
        now.getDate(),
        now.getHours(),
        0,
        0
      );

      if (now >= fetchTime && now.getMinutes() === 0) {
        fetchData();
        fetchPreviousData();
      }
    }, 60000); // Check every minute and fetch data if the minutes value is zero

    fetchData();
    fetchPreviousData();

    return () => {
      clearInterval(resetInterval);
      clearInterval(fetchInterval);
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
