# finder.py
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import re
import warnings
warnings.filterwarnings('ignore')

class TemplateFinder:
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=5000)
        # Initialize sentence transformer for semantic similarity
        try:
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        except:
            # Fallback if sentence transformers not available
            self.sentence_model = None
    
    def preprocess_text(self, text):
        """Clean and preprocess text for better matching"""
        if pd.isna(text) or text == '':
            return ''
        
        # Convert to lowercase and remove special characters
        text = str(text).lower()
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def create_client_keyword_corpus(self):
        """Create a comprehensive keyword corpus from client profiles"""
        client_profiles = self.data_loader.get_client_profiles()
        client_keywords = []
        
        for _, row in client_profiles.iterrows():
            # Combine all keyword-related fields
            keywords_text = ""
            keyword_fields = ['keywords', 'domain_url', 'industry', 'business_niche', 
                            'marketing_focus', 'relevant_keywords']
            
            for field in keyword_fields:
                if field in row and pd.notna(row[field]):
                    keywords_text += " " + str(row[field])
            
            client_keywords.append(self.preprocess_text(keywords_text))
        
        return client_keywords
    
    def create_template_corpus(self):
        """Create template corpus by combining template details with client mappings"""
        template_details = self.data_loader.get_template_details()
        template_tags = self.data_loader.get_template_tags()
        client_profiles = self.data_loader.get_client_profiles()
        
        template_corpus = []
        template_info = []
        
        # Merge template details with template tags to get client associations
        merged_templates = pd.merge(
            template_details, 
            template_tags, 
            on='template_name', 
            how='left'
        )
        
        for template_name in template_details['template_name'].unique():
            template_data = merged_templates[merged_templates['template_name'] == template_name]
            
            # Get template description
            template_desc = template_data['description'].iloc[0] if not template_data.empty else ""
            
            # Get associated clients for this template
            associated_clients = template_data['client_name'].dropna().unique()
            
            # Find keywords from client profiles for associated clients
            client_keywords = ""
            for client in associated_clients:
                client_profile = client_profiles[
                    client_profiles['client_type'].str.contains(str(client), case=False, na=False)
                ]
                
                if not client_profile.empty:
                    for _, client_row in client_profile.iterrows():
                        keyword_fields = ['keywords', 'industry', 'business_niche', 
                                        'marketing_focus', 'relevant_keywords']
                        for field in keyword_fields:
                            if field in client_row and pd.notna(client_row[field]):
                                client_keywords += " " + str(client_row[field])
            
            # Combine template description with associated client keywords
            combined_text = f"{template_desc} {client_keywords}"
            template_corpus.append(self.preprocess_text(combined_text))
            
            # Store template info
            template_info.append({
                'template_name': template_name,
                'description': template_desc,
                'associated_clients': list(associated_clients)
            })
        
        return template_corpus, template_info
    
    def calculate_tfidf_similarity(self, query, template_corpus):
        """Calculate TF-IDF based similarity"""
        processed_query = self.preprocess_text(query)
        
        if not template_corpus:
            return np.array([])
        
        # Fit TF-IDF on template corpus + query
        all_texts = template_corpus + [processed_query]
        tfidf_matrix = self.vectorizer.fit_transform(all_texts)
        
        # Calculate cosine similarity between query and templates
        query_vector = tfidf_matrix[-1]
        template_vectors = tfidf_matrix[:-1]
        similarities = cosine_similarity(query_vector, template_vectors).flatten()
        
        return similarities
    
    def calculate_semantic_similarity(self, query, template_corpus):
        """Calculate semantic similarity using sentence transformers"""
        if self.sentence_model is None or not template_corpus:
            return np.array([])
        
        processed_query = self.preprocess_text(query)
        
        try:
            # Encode all texts
            template_embeddings = self.sentence_model.encode(template_corpus)
            query_embedding = self.sentence_model.encode([processed_query])
            
            # Calculate semantic similarity
            similarities = cosine_similarity(query_embedding, template_embeddings).flatten()
            return similarities
        except Exception:
            # Fallback to empty array if encoding fails
            return np.array([])
    
    def find_similar_templates(self, query, top_k=20):
        """Find templates most similar to the query using combined similarity metrics"""
        # Create template corpus
        template_corpus, template_info = self.create_template_corpus()
        
        if not template_corpus:
            return pd.DataFrame()
        
        # Calculate TF-IDF similarity
        tfidf_similarities = self.calculate_tfidf_similarity(query, template_corpus)
        
        # Calculate semantic similarity
        semantic_similarities = self.calculate_semantic_similarity(query, template_corpus)
        
        # Combine both similarity scores (weighted average)
        if len(tfidf_similarities) > 0 and len(semantic_similarities) > 0:
            combined_similarities = (0.4 * tfidf_similarities + 0.6 * semantic_similarities)
        elif len(semantic_similarities) > 0:
            combined_similarities = semantic_similarities
        elif len(tfidf_similarities) > 0:
            combined_similarities = tfidf_similarities
        else:
            return pd.DataFrame()
        
        # Get top k recommendations
        top_indices = np.argsort(combined_similarities)[::-1][:top_k]
        
        # Create recommendations dataframe
        recommendations = self._build_recommendations_dataframe(
            top_indices, combined_similarities, template_info
        )
        
        return recommendations
    
    def _build_recommendations_dataframe(self, top_indices, similarities, template_info):
        """Build the final recommendations dataframe"""
        template_details = self.data_loader.get_template_details()
        template_tags = self.data_loader.get_template_tags()
        
        recommendations = []
        
        for idx in top_indices:
            if similarities[idx] > 0:  # Only include positive similarities
                template_name = template_info[idx]['template_name']
                
                # Get additional template details
                template_detail = template_details[
                    template_details['template_name'] == template_name
                ]
                
                if template_detail.empty:
                    continue
                
                template_detail = template_detail.iloc[0]
                
                # Get preview URL from template tags
                template_preview = template_tags[
                    template_tags['template_name'] == template_name
                ]
                preview_url = template_preview['preview_url'].iloc[0] if not template_preview.empty else ""
                
                recommendations.append({
                    'Template Name': template_name,
                    'Description': template_detail['description'],
                    'Similarity Score': round(similarities[idx] * 100, 2),
                    'Open Preview': preview_url,
                    'Associated Clients': ', '.join(template_info[idx]['associated_clients'])
                })
        
        return pd.DataFrame(recommendations)
    
    def get_template_by_client(self, client_name):
        """Get all templates associated with a specific client"""
        template_tags = self.data_loader.get_template_tags()
        template_details = self.data_loader.get_template_details()
        
        # Filter templates by client
        client_templates = template_tags[
            template_tags['client_name'].str.contains(client_name, case=False, na=False)
        ]
        
        # Merge with template details
        result = pd.merge(
            client_templates,
            template_details,
            on='template_name',
            how='left'
        )
        
        return result
    
    def get_popular_keywords(self, top_n=10):
        """Get most popular keywords from client profiles"""
        client_profiles = self.data_loader.get_client_profiles()
        all_keywords = []
        
        for _, row in client_profiles.iterrows():
            keyword_fields = ['keywords', 'industry', 'business_niche', 
                            'marketing_focus', 'relevant_keywords']
            
            for field in keyword_fields:
                if field in row and pd.notna(row[field]):
                    keywords = str(row[field]).split(',')
                    all_keywords.extend([kw.strip().lower() for kw in keywords])
        
        # Count keyword frequency
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        
        return keyword_counts.most_common(top_n)