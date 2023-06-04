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

const LineChart = () => {
  const cameraSensorRef = useRef(null);
  const dhtSensorRef = useRef(null);

  const [chartData, setChartData] = useState({
    labels: [],
    datasets: [
      {
        label: "MLX90640 Temperature",
        data: [],
        borderColor: "rgb(255, 99, 132)",
        backgroundColor: "rgba(255, 99, 132, 0.5)",
      },
      {
        label: "DHT11 Temperature",
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
        const lineChartRef = ref(db, "line_chart");
        const lineChartSnapshot = await get(lineChartRef);
        const lineChartData = lineChartSnapshot.val();

        if (lineChartData) {
          const chartDates = Object.keys(lineChartData);
          const outdatedDates = chartDates.filter((date) => date !== today);

          for (const date of outdatedDates) {
            const dateRef = ref(lineChartRef, date);
            set(dateRef, null);
          }
        }
      } catch (error) {
        console.log("Error resetting chart data: ", error);
      }
    };

    const fetchData = async () => {
      try {
        const cameraSensorSnapshot = await get(
          ref(db, `camera_sensor/roomTemp`)
        );
        const dhtSensorSnapshot = await get(ref(db, `dht_sensor/temperature`));

        const cameraSensorData = cameraSensorSnapshot.val();
        const dhtSensorData = dhtSensorSnapshot.val();

        if (cameraSensorData) {
          const cameraSensorTemperature = Math.round(cameraSensorData);
          setChartData((prevData) => ({
            ...prevData,
            datasets: [
              {
                ...prevData.datasets[0],
                data: [...prevData.datasets[0].data, cameraSensorTemperature],
              },
              prevData.datasets[1],
            ],
            labels: [...prevData.labels, getTimestampString()],
          }));
          const lineChartCameraTempRef = ref(
            db,
            `line_chart/${getTimestampString()}/camera_temperature`
          );
          set(lineChartCameraTempRef, cameraSensorTemperature);
        }

        if (dhtSensorData) {
          const dhtSensorTemperature = dhtSensorData;
          setChartData((prevData) => ({
            ...prevData,
            datasets: [
              prevData.datasets[0],
              {
                ...prevData.datasets[1],
                data: [...prevData.datasets[1].data, dhtSensorTemperature],
              },
            ],
            labels: [...prevData.labels, getTimestampString()],
          }));
          const lineChartDHTTempRef = ref(
            db,
            `line_chart/${getTimestampString()}/dht_temperature`
          );
          set(lineChartDHTTempRef, dhtSensorTemperature);
        }
      } catch (error) {
        console.log("Error fetching data: ", error);
      }
    };

    const fetchPreviousData = async () => {
      try {
        const lineChartSnapshot = await get(ref(db, `line_chart`));
        const lineChartData = lineChartSnapshot.val();

        if (lineChartData) {
          const labels = Object.keys(lineChartData);
          const cameraSensorData = labels.map(
            (label) => lineChartData[label].camera_temperature
          );
          const dhtSensorData = labels.map(
            (label) => lineChartData[label].dht_temperature
          );

          setChartData({
            labels: labels,
            datasets: [
              {
                ...chartData.datasets[0],
                data: cameraSensorData,
              },
              {
                ...chartData.datasets[1],
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
    }, 60000); // Fetch every hour

    fetchData();
    fetchPreviousData();

    return () => {
      clearInterval(resetInterval);
      clearInterval(fetchInterval);
      if (cameraSensorRef.current) off(cameraSensorRef.current);
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
        text: "Temperature Comparison",
        color: "white",
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: "Temperature (°C)",
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
    return <div>Loading Line Chart...</div>;
  }

  return (
    <div className={styles.chartBG}>
      <Line options={options} data={chartData} />
    </div>
  );
};

export default LineChart;
