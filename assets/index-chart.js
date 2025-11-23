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
        data: [14, 20, 24, 25, 29, 36, 43, 52, 55, 83, 97, 111, 128, 146, 159, 174, 192, 202, 220, 243, 267, 289, 310, 327, 340, 341]
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
        data: [341, 0, 0, 0, 0, 0, 0, 0],
        borderWidth: 0,
      },
    ],
    labels: ["Other", "Understanding (UND)", "Testing (TES)", "Measurement (MEA)", "Aging process analysis (ANA)", "Rejuvenation (REJ)", "Prediction (PRE)", "Other Mitigation Methods (OTM)"]
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