<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Portfolio Directory</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #f4f5f7;
    color: #1a1a1a;
  }
  header {
    background: #0d1117;
    color: #fff;
    padding: 40px 20px;
    text-align: center;
  }
  header h1 {
    margin: 0 0 8px;
    font-size: 2rem;
  }
  header p {
    margin: 0;
    color: #9da7b3;
    font-size: 1rem;
  }
  .container {
    max-width: 800px;
    margin: 0 auto;
    padding: 30px 20px 60px;
  }
  .card {
    background: #fff;
    border: 1px solid #e1e4e8;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: box-shadow 0.2s ease;
  }
  .card:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  }
  .card a {
    text-decoration: none;
    color: #0969da;
    font-weight: 600;
    font-size: 1.05rem;
  }
  .card a:hover {
    text-decoration: underline;
  }
  .badge {
    font-size: 0.75rem;
    color: #57606a;
    background: #eef1f4;
    padding: 4px 10px;
    border-radius: 12px;
  }
  footer {
    text-align: center;
    padding: 20px;
    color: #8b949e;
    font-size: 0.85rem;
  }
</style>
</head>
<body>

<header>
  <h1>Portfolio Directory & Generator Hub</h1>
  <p>Select a portfolio version to view or open</p>
</header>

<div class="container">
  <div class="card">
    <a href="index.html (10) - Copy.html">All-In-One Interactive Portfolio</a>
    <span class="badge">Interactive File</span>
  </div>
  <div class="card">
    <a href="index (5).html">Index 5 Portfolio Edition</a>
    <span class="badge">HTML Page</span>
  </div>
</div>

<footer>
  Hosted with GitHub Pages
</footer>

</body>
</html>
