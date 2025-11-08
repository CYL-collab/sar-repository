var barChart = document.getElementById("barChart").getContext("2d");
var pieChart = document.getElementById("pieChart").getContext("2d");

var myBarChart = new Chart(barChart, {
  type: "bar",
  data: {
    labels: ["2001", "2002", "2003", "2004", "2005", "2006", "2007", "2008", "2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"],
    datasets: [
      {
        label: "# Publications",
        backgroundColor: "rgb(23, 125, 255)",
        borderColor: "rgb(23, 125, 255)",
        data: [16, 22, 26, 27, 31, 39, 46, 57, 61, 91, 107, 121, 141, 160, 174, 189, 208, 220, 240, 264, 289, 312, 334, 350, 363, 364]
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
        data: [129, 64, 56, 33, 26, 25, 14, 12, 5],
        borderWidth: 0,
      },
    ],
    labels: ["Model-based Analysis", "Measurement-based Analysis", "Indicator", "Hybrid Analysis", "Rejuvenation", "ARB Prediction", "Other", "Testing", "Other Mitigation"]
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