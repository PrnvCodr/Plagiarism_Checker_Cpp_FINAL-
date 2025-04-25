import streamlit as st
import re
import os
import hashlib
from collections import defaultdict, Counter
import difflib
import tempfile

class CPPSimilarityChecker:
    def __init__(self):
        self.ignore_comments = True
        self.ignore_whitespace = True
        self.normalize_identifiers = True
        
    def load_cpp_file(self, file_path):
        """Load a C++ file from the given path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found")
            
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()
    
    def preprocess_cpp(self, code):
        """Preprocess C++ code by removing comments, normalizing whitespace, etc."""
        # Remove C and C++ style comments
        if self.ignore_comments:
            # Remove C-style comments (/* */)
            code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
            # Remove C++-style comments (//)
            code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
        
        # Remove extra whitespace
        if self.ignore_whitespace:
            # Replace multiple whitespace with single space
            code = re.sub(r'\s+', ' ', code)
            # Remove whitespace around operators
            code = re.sub(r'\s*([=+\-*/(){}[\];<>!&|,.])\s*', r'\1', code)
        
        # Normalize variable identifiers if requested
        if self.normalize_identifiers:
            # Extract tokens, preserving structure
            tokens = []
            current_token = ""
            identifier_counter = 0
            identifier_map = {}
            
            # Tokenize code
            i = 0
            while i < len(code):
                char = code[i]
                
                # Identifier or keyword
                if char.isalpha() or char == '_':
                    start = i
                    while i < len(code) and (code[i].isalnum() or code[i] == '_'):
                        i += 1
                    word = code[start:i]
                    
                    # Check if it's a C++ keyword
                    cpp_keywords = {"auto", "break", "case", "char", "const", "continue", 
                                   "default", "do", "double", "else", "enum", "extern", 
                                   "float", "for", "goto", "if", "int", "long", "register", 
                                   "return", "short", "signed", "sizeof", "static", "struct", 
                                   "switch", "typedef", "union", "unsigned", "void", "volatile", 
                                   "while", "class", "namespace", "try", "catch", "new", 
                                   "delete", "public", "private", "protected", "template", 
                                   "virtual", "friend", "inline", "operator", "using", "throw"}
                    
                    if word in cpp_keywords:
                        tokens.append(word)
                    else:
                        # Normalize identifiers
                        if word not in identifier_map:
                            identifier_map[word] = f"VAR_{identifier_counter}"
                            identifier_counter += 1
                        tokens.append(identifier_map[word])
                    continue
                
                # Number literals
                elif char.isdigit():
                    start = i
                    while i < len(code) and (code[i].isdigit() or code[i] == '.'):
                        i += 1
                    tokens.append("NUM")
                    continue
                
                # String literals
                elif char == '"' or char == "'":
                    quote = char
                    start = i
                    i += 1
                    while i < len(code) and code[i] != quote:
                        if code[i] == '\\' and i + 1 < len(code):
                            i += 2
                        else:
                            i += 1
                    if i < len(code):
                        i += 1  # Skip closing quote
                    tokens.append("STR")
                    continue
                
                # Other characters (operators, brackets, etc.)
                else:
                    tokens.append(char)
                    i += 1
            
            return ' '.join(tokens)
        
        return code
    
    def calculate_moss_similarity(self, code1, code2, k=5, w=10):
        """
        Calculate MOSS similarity between two code snippets.
        
        Args:
            code1, code2: Input code snippets
            k: k-gram size
            w: Window size for winnowing
        
        Returns:
            Similarity score between 0 and 1
        """
        # Get k-grams and their hashes for each code
        def get_kgram_hashes(code, k):
            tokens = code.split()
            if len(tokens) < k:
                return []
            
            # Generate k-grams
            kgrams = [' '.join(tokens[i:i+k]) for i in range(len(tokens)-k+1)]
            
            # Hash each k-gram
            kgram_hashes = [int(hashlib.md5(kgram.encode()).hexdigest(), 16) for kgram in kgrams]
            
            return kgram_hashes
        
        # Apply winnowing algorithm to select fingerprints
        def winnow(hashes, w):
            if len(hashes) < w:
                return hashes
                
            windows = [hashes[i:i+w] for i in range(len(hashes)-w+1)]
            fingerprints = []
            
            for i, window in enumerate(windows):
                # Find minimum hash in window and its position
                min_hash = min(window)
                min_pos = window.index(min_hash) + i
                
                # Add to fingerprints if not already added or at different position
                if not fingerprints or fingerprints[-1][0] != min_hash:
                    fingerprints.append((min_hash, min_pos))
                    
            # Extract just the hash values
            return [h for h, pos in fingerprints]
        
        # Get preprocessed code
        processed_code1 = self.preprocess_cpp(code1)
        processed_code2 = self.preprocess_cpp(code2)
        
        # Get hashes and fingerprints for each code snippet
        hashes1 = get_kgram_hashes(processed_code1, k)
        hashes2 = get_kgram_hashes(processed_code2, k)
        
        # Apply winnowing to select fingerprints
        fingerprints1 = set(winnow(hashes1, w))
        fingerprints2 = set(winnow(hashes2, w))
        
        # Calculate similarity
        if not fingerprints1 or not fingerprints2:
            return 0
            
        intersection = fingerprints1.intersection(fingerprints2)
        union = fingerprints1.union(fingerprints2)
        similarity = len(intersection) / len(union)
        
        return similarity
    
    def calculate_structure_similarity(self, code1, code2):
        """Calculate structural similarity between two code samples."""
        # Helper to extract function/class structure
        def extract_structure(code):
            # Extract function declarations
            function_pattern = r'\w+\s+(\w+)\s*\([^)]*\)\s*{[^}]*}'
            functions = re.findall(function_pattern, code)
            
            # Extract class declarations
            class_pattern = r'class\s+(\w+)[^{]*{[^}]*}'
            classes = re.findall(class_pattern, code)
            
            # Extract control structures (simplified)
            control_structures = []
            for ctrl in ['if', 'else', 'for', 'while', 'switch', 'case']:
                count = len(re.findall(rf'\b{ctrl}\b', code))
                control_structures.append((ctrl, count))
            
            return {
                'functions': Counter(functions),
                'classes': Counter(classes),
                'control_structures': dict(control_structures)
            }
        
        # Extract structure from both code samples
        structure1 = extract_structure(code1)
        structure2 = extract_structure(code2)
        
        # Calculate similarity for functions and classes
        def count_similarity(counter1, counter2):
            if not counter1 and not counter2:
                return 1.0
            if not counter1 or not counter2:
                return 0.0
            
            common = sum((counter1 & counter2).values())
            total = sum((counter1 | counter2).values())
            return common / total if total > 0 else 0
        
        # Calculate control structure similarity
        def control_similarity(ctrl1, ctrl2):
            all_keys = set(ctrl1.keys()) | set(ctrl2.keys())
            if not all_keys:
                return 1.0
                
            differences = 0
            max_possible_diff = 0
            
            for key in all_keys:
                val1 = ctrl1.get(key, 0)
                val2 = ctrl2.get(key, 0)
                max_val = max(val1, val2)
                differences += abs(val1 - val2)
                max_possible_diff += max_val
            
            return 1 - (differences / max_possible_diff if max_possible_diff > 0 else 0)
        
        # Calculate individual similarities
        func_sim = count_similarity(structure1['functions'], structure2['functions'])
        class_sim = count_similarity(structure1['classes'], structure2['classes'])
        ctrl_sim = control_similarity(structure1['control_structures'], structure2['control_structures'])
        
        # Weighted average
        return 0.4 * func_sim + 0.3 * class_sim + 0.3 * ctrl_sim
    
    def calculate_line_similarity(self, code1, code2):
        """Calculate line-by-line similarity using difflib."""
        # Split code into lines
        lines1 = self.preprocess_cpp(code1).split('\n')
        lines2 = self.preprocess_cpp(code2).split('\n')
        
        # Use difflib to calculate similarity
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        return matcher.ratio()
    
    def check_similarity(self, code1, code2):
        """Check similarity between two C++ code strings."""
        try:
            # Calculate similarities using different methods
            moss_sim = self.calculate_moss_similarity(code1, code2)
            structure_sim = self.calculate_structure_similarity(code1, code2)
            line_sim = self.calculate_line_similarity(code1, code2)
            
            # Weight different metrics
            overall_sim = 0.5 * moss_sim + 0.3 * structure_sim + 0.2 * line_sim
            
            # Determine similarity level
            if overall_sim >= 0.8:
                similarity_level = "Very High"
            elif overall_sim >= 0.6:
                similarity_level = "High"
            elif overall_sim >= 0.4:
                similarity_level = "Moderate"
            elif overall_sim >= 0.2:
                similarity_level = "Low"
            else:
                similarity_level = "Very Low"
            
            # Identify suspicious code segments
            suspicious_segments = self.identify_similar_segments(code1, code2)
            
            # Prepare report
            report = {
                'summary': {
                    'similarity_level': similarity_level,
                    'overall_similarity': overall_sim,
                },
                'details': {
                    'moss_similarity': moss_sim,
                    'structure_similarity': structure_sim,
                    'line_similarity': line_sim,
                },
                'suspicious_segments': suspicious_segments[:5]  # Top 5 suspicious segments
            }
            
            return report
            
        except Exception as e:
            return {'error': str(e)}
    
    def identify_similar_segments(self, code1, code2, min_length=3):
        """Identify similar code segments between the two files."""
        # Process code
        processed1 = self.preprocess_cpp(code1)
        processed2 = self.preprocess_cpp(code2)
        
        # Split into lines
        lines1 = processed1.split('\n')
        lines2 = processed2.split('\n')
        
        # Use difflib to find matching blocks
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        matching_blocks = matcher.get_matching_blocks()
        
        suspicious_segments = []
        
        # Filter meaningful blocks (longer than min_length)
        for block in matching_blocks:
            i, j, size = block
            if size >= min_length:
                # Get original code segments
                original_lines1 = code1.split('\n')
                original_lines2 = code2.split('\n')
                
                # Ensure we don't go out of bounds
                i_end = min(i + size, len(original_lines1))
                j_end = min(j + size, len(original_lines2))
                
                segment1 = '\n'.join(original_lines1[i:i_end])
                segment2 = '\n'.join(original_lines2[j:j_end])
                
                suspicious_segments.append({
                    'file1_start_line': i + 1,  # 1-indexed for display
                    'file2_start_line': j + 1,
                    'length': size,
                    'file1_segment': segment1,
                    'file2_segment': segment2,
                    'similarity': difflib.SequenceMatcher(None, segment1, segment2).ratio()
                })
        
        # Sort by similarity (highest first)
        suspicious_segments.sort(key=lambda x: x['similarity'], reverse=True)
        
        return suspicious_segments

def save_uploaded_file(uploaded_file):
    """Save the uploaded file to a temporary location and return the path"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.cpp') as temp_file:
        temp_file.write(uploaded_file.getvalue())
        return temp_file.name

def main():
    st.set_page_config(
        page_title="C++ Code Similarity Checker",
        page_icon="🔍",
        layout="wide",
    )
    
    st.title("C++ Code Similarity Checker")
    st.markdown("""
    This tool checks similarity between two C++ files using multiple algorithms including MOSS, 
    structure analysis, and line-by-line comparison.
    """)
    
    # Create tabs for different input methods
    tab1, tab2 = st.tabs(["Upload Files", "Paste Code"])
    
    # File uploader tab
    with tab1:
        st.header("Upload C++ Files")
        col1, col2 = st.columns(2)
        
        with col1:
            file1 = st.file_uploader("Upload first C++ file", type=["cpp", "h", "hpp", "cc"])
        
        with col2:
            file2 = st.file_uploader("Upload second C++ file", type=["cpp", "h", "hpp", "cc"])
    
    # Code pasting tab
    with tab2:
        st.header("Paste C++ Code")
        col1, col2 = st.columns(2)
        
        with col1:
            code1 = st.text_area("First C++ code:", height=300)
        
        with col2:
            code2 = st.text_area("Second C++ code:", height=300)
    
    # Options expander
    with st.expander("Advanced Options"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ignore_comments = st.checkbox("Ignore comments", value=True)
        
        with col2:
            ignore_whitespace = st.checkbox("Ignore whitespace", value=True)
        
        with col3:
            normalize_identifiers = st.checkbox("Normalize identifiers", value=True)
    
    # Analysis button
    analyze_button = st.button("Analyze Similarity", type="primary")
    
    if analyze_button:
        # Initialize checker with options
        checker = CPPSimilarityChecker()
        checker.ignore_comments = ignore_comments
        checker.ignore_whitespace = ignore_whitespace
        checker.normalize_identifiers = normalize_identifiers
        
        # Get code from either files or text areas
        try:
            if 'file1' in locals() and file1 is not None and 'file2' in locals() and file2 is not None:
                # Save uploaded files to temp location
                temp_file1 = save_uploaded_file(file1)
                temp_file2 = save_uploaded_file(file2)
                
                # Load code from temp files
                with open(temp_file1, 'r', encoding='utf-8', errors='ignore') as f:
                    code1_content = f.read()
                with open(temp_file2, 'r', encoding='utf-8', errors='ignore') as f:
                    code2_content = f.read()
                    
                # Clean up temp files
                os.unlink(temp_file1)
                os.unlink(temp_file2)
                
                file1_name = file1.name
                file2_name = file2.name
                
            elif 'code1' in locals() and code1 and 'code2' in locals() and code2:
                code1_content = code1
                code2_content = code2
                file1_name = "Code Snippet 1"
                file2_name = "Code Snippet 2"
                
            else:
                st.error("Please upload both files or paste code in both text areas.")
                st.stop()
                
            # Show a spinner while processing
            with st.spinner("Analyzing code similarity..."):
                # Check similarity
                report = checker.check_similarity(code1_content, code2_content)
                
            if 'error' in report:
                st.error(f"Error during comparison: {report['error']}")
                st.stop()
                
            # Display results
            st.success("Analysis complete!")
            
            # Results section
            st.header("Similarity Report")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Overall Similarity", f"{report['summary']['overall_similarity']:.2f}")
            
            with col2:
                st.metric("Similarity Level", report['summary']['similarity_level'])
            
            # Visual indicator
            similarity = report['summary']['overall_similarity']
            st.progress(similarity)
            
            # Detailed metrics
            st.subheader("Detailed Metrics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("MOSS Similarity", f"{report['details']['moss_similarity']:.2f}")
            
            with col2:
                st.metric("Structure Similarity", f"{report['details']['structure_similarity']:.2f}")
            
            with col3:
                st.metric("Line Similarity", f"{report['details']['line_similarity']:.2f}")
            
            # Suspicious segments
            st.subheader("Suspicious Code Segments")
            
            if report['suspicious_segments']:
                for i, segment in enumerate(report['suspicious_segments']):
                    with st.expander(f"Segment {i+1} (Similarity: {segment['similarity']:.2f})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"**{file1_name}** (Line {segment['file1_start_line']})")
                            st.code(segment['file1_segment'], language="cpp")
                        
                        with col2:
                            st.markdown(f"**{file2_name}** (Line {segment['file2_start_line']})")
                            st.code(segment['file2_segment'], language="cpp")
            else:
                st.info("No significant matching segments found.")
                
            # Interpretation guide
            with st.expander("Interpretation Guide"):
                st.markdown("""
                ### Similarity Level
                - **Very High (0.8-1.0)**: Files are nearly identical or heavily plagiarized
                - **High (0.6-0.8)**: Significant code sharing or common implementation
                - **Moderate (0.4-0.6)**: Some similar code structures or algorithms
                - **Low (0.2-0.4)**: Minor similarities, possibly coincidental
                - **Very Low (0.0-0.2)**: Files are substantially different

                ### Metrics
                - **MOSS Similarity**: Based on code fingerprinting, detects structural similarities even with variable name changes
                - **Structure Similarity**: Analyzes function/class structure and control flow patterns
                - **Line Similarity**: Direct line-by-line comparison of preprocessed code
                """)
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()