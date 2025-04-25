# 🔍 Plagiarism Checker for C++

An advanced plagiarism detection tool specifically designed for **C++ code**, leveraging multiple similarity detection algorithms to provide comprehensive analysis and reliable results.

---

## 🚀 Features

- **🧠 Multi-Algorithm Analysis**: Combines 5 different similarity detection methods for accurate plagiarism detection  
- **🖼️ Code Visualization**: Highlights matching code segments for easy comparison  
- **🧹 Preprocessing**: Normalizes code to detect plagiarism even with variable name changes and formatting differences  
- **📊 Detailed Reporting**: Provides similarity scores and specific matching sections  
- **🌐 Web Interface**: Easy-to-use interface built with Streamlit  

---

## ⚙️ How It Works

The plagiarism checker uses a **sophisticated ensemble of algorithms** to detect similarities between C++ code samples:

### 1. 🧬 MOSS-Style Winnowing Algorithm (50% weight)
Based on the renowned **MOSS (Measure of Software Similarity)** system developed at Stanford:

- **K-gram Tokenization**: Breaks code into overlapping sequences of *k = 5* tokens  
- **MD5 Hashing**: Creates unique fingerprints for each k-gram  
- **Winnowing**: Uses a sliding window (*w = 10*) to select representative hashes  
- **Fingerprint Matching**: Compares fingerprints to detect matching regions  

### 2. 🧱 AST-Like Structure Analysis (30% weight)

Analyzes the **structural skeleton** of the code to detect logic-level similarities:

- **Function/Class Extraction**  
- **Control Structure Counting**: (if, else, for, while, etc.)  
- **Jaccard-Like Scoring**: Based on shared structural elements  

### 3. 📏 Line-by-Line Sequence Matching (20% weight)

Compares code using the **Ratcliff/Obershelp algorithm**:

- **Sequence Matching**: via Python's `difflib.SequenceMatcher`  
- **Block Detection**: Highlights matching code blocks  
- **Visualization**: Line-by-line comparison output  

### 4. 🔧 Advanced Preprocessing

Detects plagiarism even after superficial changes:

- **Comment Removal**  
- **Whitespace Normalization**  
- **Variable Name Normalization** → `VAR_#`  
- **Literal Replacement** → `NUM`, `STR`  

### 5. ⚖️ Weighted Ensemble Scoring

Final similarity score based on:

- 50% → MOSS similarity  
- 30% → Structure similarity  
- 20% → Line similarity  

---

## 🎯 Similarity Rating Scale

| Score Range | Level         |
|-------------|---------------|
| 0.00–0.20   | Very Low      |
| 0.20–0.40   | Low           |
| 0.40–0.60   | Moderate      |
| 0.60–0.80   | High          |
| 0.80–1.00   | Very High     |

---

## 🧪 Usage

1. **Visit the Plagiarism Checker App**  
2. **Upload or Paste** two C++ code samples  
3. Click **"Check Similarity"**  
4. View similarity **scores and visual highlights**

---

## 🧰 Technical Implementation

- **Frontend**: [Streamlit](https://streamlit.io)  
- **Backend**: Python  
- **Core Algorithms**:
  - MOSS-style fingerprinting
  - Structure comparison
  - Sequence matching

---

## ⚠️ Limitations

- Optimized specifically for **C++**
- May miss **extremely obfuscated** code
- Processing time increases with code size and complexity

---

## 🤝 Contributing

Contributions are welcome!  
Feel free to fork the project and submit a **Pull Request**.

---

## 📄 License

This project is licensed under the **MIT License**.  
See the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- Inspired by the **MOSS** system from Stanford University  
- Built with ❤️ using **Python** and **Streamlit**
