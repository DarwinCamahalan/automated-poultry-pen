import React, { useEffect, useState } from "react";
import Link from "next/link";
import styles from "./graphs.module.scss";
import { Line } from "react-chartjs-2";
import { app, db } from "../firebaseConfig";
import { get, ref } from "firebase/database";
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

const AllGraphs = () => {
  const [temperatureChartData, setTemperatureChartData] = useState([]);
  const [humidityChartData, setHumidityChartData] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const temperatureSnapshot = await get(
          ref(db, "manual_edit_line_graph/temperatures")
        );
        const temperatureData = temperatureSnapshot.val();
        if (temperatureData) {
          const temperatureCharts = Object.values(temperatureData)
            .slice(1)
            .map((chartData, index) => ({
              id: index + 1,
              data: formatTemperatureChartData(chartData),
            }));
          setTemperatureChartData(temperatureCharts);
        } else {
          setTemperatureChartData([]);
        }

        const humiditySnapshot = await get(
          ref(db, "manual_edit_line_graph/humidity")
        );
        const humidityData = humiditySnapshot.val();
        if (humidityData) {
          const humidityCharts = Object.values(humidityData)
            .slice(1)
            .map((chartData, index) => ({
              id: index + 1,
              data: formatHumidityChartData(chartData),
            }));
          setHumidityChartData(humidityCharts);
        } else {
          setHumidityChartData([]);
        }
      } catch (error) {
        console.log("Error fetching data: ", error);
      }
    };

    // Register the scales and elements individually
    Chart.register(
      CategoryScale,
      LinearScale,
      PointElement,
      LineElement,
      Title,
      Tooltip,
      Legend
    );

    fetchData();
  }, []);

  // Helper function to format temperature chart data
  const formatTemperatureChartData = (chartData) => {
    const timeLabels = [
      "9:00 AM",
      "10:00 AM",
      "11:00 AM",
      "12:00 PM",
      "1:00 PM",
      "2:00 PM",
      "3:00 PM",
      "4:00 PM",
      "5:00 PM",
      "6:00 PM",
      "7:00 PM",
      "8:00 PM",
      "9:00 PM",
      "10:00 PM",
      "11:00 PM",
      "12:00 AM",
    ];

    const cameraTemperatureData = Object.values(chartData).map(
      (entry) => entry.camera_temperature
    );
    const dhtTemperatureData = Object.values(chartData).map(
      (entry) => entry.dht_temperature
    );

    return {
      labels: timeLabels,
      datasets: [
        {
          label: "MLX90640 Temperature",
          data: cameraTemperatureData,
          fill: false,
          borderColor: "rgb(255, 99, 132)",
          tension: 0.1,
        },
        {
          label: "DHT11 Temperature",
          data: dhtTemperatureData,
          fill: false,
          borderColor: "rgb(53, 162, 235)",
          tension: 0.1,
        },
      ],
    };
  };

  // Helper function to format humidity chart data
  const formatHumidityChartData = (chartData) => {
    const timeLabels = [
      "9:00 AM",
      "10:00 AM",
      "11:00 AM",
      "12:00 PM",
      "1:00 PM",
      "2:00 PM",
      "3:00 PM",
      "4:00 PM",
      "5:00 PM",
      "6:00 PM",
      "7:00 PM",
      "8:00 PM",
      "9:00 PM",
      "10:00 PM",
      "11:00 PM",
      "12:00 AM",
    ];

    const humidityData = Object.values(chartData).map(
      (entry) => entry.humidity
    );

    return {
      labels: timeLabels,
      datasets: [
        {
          label: "Humidity",
          data: humidityData,
          fill: false,
          borderColor: "rgb(75, 192, 192)",
          tension: 0.1,
        },
      ],
    };
  };

  return (
    <div className={styles.chartBG}>
      <h2>Temperature Charts</h2>
      <div className={styles.chart}>
        {temperatureChartData.length > 0
          ? temperatureChartData.map(({ id, data }) => (
              <div key={id} className={styles.tempChart}>
                <h3>Day {id}</h3>
                <Line
                  data={data}
                  options={{
                    maintainAspectRatio: false,
                    color: "white",
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: "top",
                        labels: {
                          color: "white",
                        },
                      },
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        title: {
                          display: true,
                          text: "Temperature",
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
                  }}
                />
              </div>
            ))
          : null}
      </div>
      <h2>Humidity Charts</h2>
      <div className={styles.chart}>
        {humidityChartData.length > 0
          ? humidityChartData.map(({ id, data }) => (
              <div key={id} className={styles.humidityChart}>
                <h1>Day {id}</h1>
                <Line
                  data={data}
                  options={{
                    maintainAspectRatio: false,
                    color: "white",
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: "top",
                        labels: {
                          color: "white",
                        },
                      },
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        title: {
                          display: true,
                          text: "Humidity",
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
                  }}
                />
              </div>
            ))
          : null}
      </div>

      <div className={styles.graphs}>
        <Link href="/">Go Back</Link>
      </div>
    </div>
  );
};

export default AllGraphs;
