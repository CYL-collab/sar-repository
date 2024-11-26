var barChart = document.getElementById("barChart").getContext("2d");
var pieChart = document.getElementById("pieChart").getContext("2d");

var myBarChart = new Chart(barChart, {
  type: "bar",
  data: {
    labels: ["2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007", "2008", "2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"],
    datasets: [
      {
        label: "# Publications",
        backgroundColor: "rgb(23, 125, 255)",
        borderColor: "rgb(23, 125, 255)",
        data: [17, 25, 31, 36, 39, 46, 51, 60, 75, 79, 105, 121, 132, 147, 163, 176, 188, 205, 216, 227, 253, 282, 306, 327, 330]
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      yAxes: [
        {
          ticks: {
            beginAtZero: true,
          },
        },
      ],
      x: {
        grid: {
          display: false,
        }
      },
    },
    plugins: {
      legend: {
        display: false,
      },
    },
  },
});

var myPieChart = new Chart(pieChart, {
  type: "pie",
  data: {
    datasets: [
      {
        data: [149, 45, 42, 19, 11, 11, 8, 4],
        borderWidth: 0,
      },
    ],
    labels: ["Analysis", "Indicator", "Rejuvenation", "ARB Prediction", "Classification", "Testing", "Other Mitigation", "Other"]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    pieceLabel: {
      render: "percentage",
      fontColor: "white",
      fontSize: 14,
    },
    tooltips: true,
    plugins: {
      legend: {
        position: 'bottom',
      },
    },
  },
});