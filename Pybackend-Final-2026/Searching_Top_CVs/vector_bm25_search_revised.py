"""
/******************************************************************************************************************************************************************************
 *
 *                          Solution: Smart-Recruitment(Python)
 *                          Description: Searches within the collection for the top candidates according to the parameters/filters set up by the user
 *                          Created Date: March 27, 2025
 *                          Created By: Areeb Khan
 *                          Last Updated Date: March 27, 2025
 *                          Last Updated By: Areeb Khan
 *                          Version: 1.0
 *
 ********************************************************************************************************************************************************************************/
"""
import math
import os
import re
import docx
import PyPDF2
import nltk
from rank_bm25 import BM25Okapi, BM25Plus
from nltk.tokenize import word_tokenize
from pprint import pprint
import sys
import chromadb
from sentence_transformers import SentenceTransformer
from chromadb.utils import embedding_functions
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher
import numpy as np
import time
import asyncio
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from flashtext import KeywordProcessor

load_dotenv()

nltk.download('punkt')

chromadb_host = os.getenv('CHROMADB_HOST')
chromadb_port = int(os.getenv('CHROMADB_PORT'))

# "smart_recruitment" collection
# chroma_collection = os.getenv('COLLECTION_NAME')

# "test_recruitment" collection
# chroma_collection = os.getenv('TEST_COLLECTION_NAME')

# "test2_recruitment" collection
# chroma_collection = os.getenv('TEST2_COLLECTION_NAME')

# "test3_recruitment" and "smart_recruitment_768_128_48" are essentially the same type of collection except "test3_recruitment" is used for development and the other is for production

# "test3_recruitment" collection
chroma_collection = os.getenv('TEST3_COLLECTION_NAME')

# "smart_recruitment_768_128_48" collection
# chroma_collection = os.getenv('SR_768_128_48_COLLECTION_NAME')

# Some functions are asynchronously defined because they need to "await" when calling the chromadb client to use/manipulate the collection

async def initialize_chromadb_client():
    client = await chromadb.AsyncHttpClient(host=chromadb_host, port=chromadb_port)
    collection_name = chroma_collection
    collection = await client.get_collection(name=collection_name)
    return collection

# Models that can be utilized for the vector embedding for the search query

# model = SentenceTransformer('all-MiniLM-L6-v2')
# model = SentenceTransformer("hkunlp/instructor-xl")
# model = SentenceTransformer("intfloat/e5-large-v2")
# model = SentenceTransformer("BAAI/bge-large-en-v1.5")
# model = SentenceTransformer("sentence-transformers/paraphrase-mpnet-base-v2")
model = SentenceTransformer('sentence-transformers/msmarco-distilbert-base-v4')

def custom_tokenize(text, boolean_synonym):
    """
    Optimized version of custom_tokenize with improved processing time and accuracy.
    """
    # Step 1: Initialize KeywordProcessor
    keyword_processor = KeywordProcessor(case_sensitive=False)
    synonym_to_boolean = {}

    # Add synonyms to KeywordProcessor and group multi-word synonyms by length
    multi_word_synonyms = {}
    for boolean_name, synonyms in boolean_synonym.items():
        for synonym in synonyms:
            keyword_processor.add_keyword(synonym.lower(), boolean_name.replace(" ", "_"))
            synonym_to_boolean[synonym.lower()] = boolean_name
            if " " in synonym:
                length = len(synonym.split())
                if length not in multi_word_synonyms:
                    multi_word_synonyms[length] = []
                multi_word_synonyms[length].append((synonym.lower(), boolean_name))

    # Step 2: Extract matches using KeywordProcessor
    matches = keyword_processor.extract_keywords(text.lower())

    # Step 3: Tokenize the text
    tokens = word_tokenize(text.lower())
    phrase_tokens = []
    match_set = set(matches)  # Convert matches to a set for faster lookup

    # Step 4: Process tokens using a sliding window for multi-word matching
    i = 0
    while i < len(tokens):
        matched = False

        # Check multi-word synonyms using a sliding window
        for length, synonyms in multi_word_synonyms.items():
            if i + length <= len(tokens):
                window = " ".join(tokens[i:i + length])
                for synonym, boolean_name in synonyms:
                    if window == synonym:
                        phrase_tokens.append(boolean_name.replace(" ", "_"))  # Use Boolean Name as token
                        i += length
                        matched = True
                        break
            if matched:
                break

        if not matched:
            # If the token is part of a single-word match, add it
            if tokens[i] in match_set:
                phrase_tokens.append(tokens[i])
            else:
                # Otherwise, add the token as-is
                phrase_tokens.append(tokens[i])
            i += 1

    return phrase_tokens

def filter_job_title(results, job_title, compare_all_titles, similarity_threshold=0.5):
    """
    Filters candidates based on job title similarity.
    :param results: The list of candidates with metadata.
    :param job_title: The inputted job title from the frontend.
    :param similarity_threshold: The minimum similarity score to include a candidate.
    :param compare_all_titles: If True, compare both most recent and previous job titles.
    :return: Filtered list of candidates.
    """
    print(f"Starting job title filtering. Inputted job title: {job_title}")
    print(f"Similarity threshold: {similarity_threshold}, Compare all titles: {compare_all_titles}")

    if job_title == "N/A":
        print("Job title is N/A. Skipping job title filter.")
        return results

    filtered_results = []
    for metadata in results['metadatas']:
        # Get the most recent job title
        most_recent_job_title = metadata.get('most_recent_job_title', '').lower()
        # Get the previous job titles as a list
        previous_job_titles = metadata.get('previous_job_titles', '').split("~~")

        print(f"Processing candidate: {metadata.get('filename', 'Unknown')}")
        print(f"Most recent job title: {most_recent_job_title}")
        print(f"Previous job titles: {previous_job_titles}")

        # Path 1: Compare only the most recent job title
        if compare_all_titles or not any(previous_job_titles):  # Fallback if previous_job_titles is empty
            if most_recent_job_title:
                similarity = SequenceMatcher(None, job_title.lower(), most_recent_job_title).ratio()
                print(f"Similarity with most recent job title: {similarity}")
                if similarity >= similarity_threshold:
                    print(f"Candidate passed the filter with most recent job title. Similarity: {similarity}")
                    filtered_results.append(metadata)
                else:
                    print(f"Candidate failed the filter with most recent job title. Similarity: {similarity}")

        # Path 2: Compare both most recent and previous job titles
        else:
            most_recent_similarity = 0
            previous_titles_similarity = 0

            # Compare the most recent job title
            if most_recent_job_title:
                most_recent_similarity = SequenceMatcher(None, job_title.lower(), most_recent_job_title).ratio()
                print(f"Similarity with most recent job title: {most_recent_similarity}")

            # Compare the previous job titles
            if previous_job_titles and any(previous_job_titles):  # Ensure the list is not empty or contains only empty strings
                previous_titles_similarity = max(
                    SequenceMatcher(None, job_title.lower(), prev_title.lower()).ratio()
                    for prev_title in previous_job_titles if prev_title
                )
                print(f"Highest similarity with previous job titles: {previous_titles_similarity}")

            # Determine the highest similarity score
            max_similarity = max(most_recent_similarity, previous_titles_similarity)
            print(f"Max similarity score: {max_similarity}")

            # Add the candidate to the filtered results if the similarity exceeds the threshold
            if max_similarity >= similarity_threshold:
                print(f"Candidate passed the filter. Max similarity: {max_similarity}")
                filtered_results.append(metadata)
            else:
                print(f"Candidate failed the filter. Max similarity: {max_similarity}")

    print(f"Filtering complete. Total candidates passing the filter: {len(filtered_results)}")
    return filtered_results

async def initialize_bm25_from_chromadb(collection, compare_all_titles, word, keywords_with_weights, boolean_synonym, pool_value, min_experience=None, max_experience=None, lambda_factor=0.05):
    global bm25, resume_filenames, resume_texts
    resume_filenames = []
    resume_texts = []

    # semantic_search_start_time = time.time()
    # top_filenames = await vector_rank_list(collection, word, pool_value, min_experience, max_experience, lambda_factor)
    # semantic_search_end_time = time.time()
    # semantic_search_execution_time = semantic_search_end_time - semantic_search_start_time
    # print(f"Time taken for semantic search: {semantic_search_execution_time:.2f} seconds")

    # Step 1: Parse the job title for the first semantic search
    parsed_job_title = word.split("with skills in")[0].strip()  # Extract everything before "with skills in"
    print(f"Parsed job title for first semantic search: {parsed_job_title}")

    first_pool_value = int(os.getenv('FIRST_POOL_VALUE'))

    # Step 2: First Semantic Search with Parsed Job Title
    print("Performing first semantic search with parsed job title...")
    first_search_start_time = time.time()
    top_filenames_initial = await vector_rank_list(
        collection,
        parsed_job_title,
        first_pool_value,
        min_experience,
        max_experience,
        lambda_factor
    )
    first_search_end_time = time.time()
    print(f"Time taken for first semantic search: {first_search_end_time - first_search_start_time:.2f} seconds")
    print(f"Initial candidates from first search: {len(top_filenames_initial)}")

    # Step 3: Filter the collection based on the results of the first search
    print("Filtering collection based on first search results...")
    if not top_filenames_initial:
        raise ValueError("No candidates found in the first semantic search. Please refine your query.")

    filtered_results = await collection.get(
        where={"filename": {"$in": top_filenames_initial}},  # Filter by filenames from the first search
        include=["metadatas", "embeddings"]  # OPT: documents are not used in second semantic ranking
    )

    # print(f"Filtered Results: {filtered_results}")

    # Step 4: Second Semantic Search with Full Job Title
    print("Performing second semantic search with full job title...")
    second_search_start_time = time.time()

    # Use the filtered results for the second semantic search
    query_embedding = model.encode(word).reshape(1, -1)  # Ensure query embedding is a 2D array
    second_search_results = []

    for metadata, document_embedding in zip(filtered_results['metadatas'], filtered_results['embeddings']):
        if document_embedding is not None:
            # Convert the document embedding to a NumPy array and reshape it to 2D
            document_embedding = np.array(document_embedding).reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(query_embedding, document_embedding)[0][0]
            second_search_results.append((metadata['filename'], similarity))
        else:
            print(f"Warning: No embedding found for document {metadata.get('filename')}")

    # Sort the results by similarity (descending, as higher similarity = better match)
    second_search_results = sorted(second_search_results, key=lambda x: x[1], reverse=True)
    top_filenames = [filename for filename, _ in second_search_results[:pool_value]]

    if not top_filenames:
        raise ValueError("No candidates found in the second semantic search. Please refine your query.")

    second_search_end_time = time.time()
    print(f"Time taken for second semantic search: {second_search_end_time - second_search_start_time:.2f} seconds")
    print(f"Refined candidates from second search: {len(top_filenames)}")

    print("Filtering candidates by job title...")
    # job_title_filtered_results = filter_job_title(filtered_results, parsed_job_title, similarity_threshold=0.7)
    job_title_filtered_results = filter_job_title(
        {
            "metadatas": [
                metadata for metadata, _ in sorted(
                    zip(filtered_results['metadatas'], second_search_results),
                    key=lambda x: x[1][1],  # Sort by similarity score from the second search
                    reverse=True
                )
            ]
        },
        parsed_job_title,
        compare_all_titles,
        similarity_threshold=0.5
    )
    print(f"Candidates after job title filtering: {len(job_title_filtered_results)}")

    if not job_title_filtered_results:
        print("No candidates found after job title filtering. Running fallback logic to retrieve candidates from the second semantic search.")
        
        # Fallback: Use the results from the second semantic search
        results = await collection.get(
            where={"filename": {"$in": top_filenames}},  # Filter by top filenames
            include=["documents", "metadatas"]
        )
    else:
        results = await collection.get(
            where={"filename": {"$in": [metadata['filename'] for metadata in job_title_filtered_results]}},  # Filter by top filenames
            include=["documents", "metadatas"]
        )

    for document, metadata in zip(results['documents'], results['metadatas']):
        candidate_id = metadata.get('filename', 'N/A')
        tokenized_text = metadata.get('tokenized_text', None)

        if candidate_id in top_filenames:
            if tokenized_text:
                tokenized_text_list = tokenized_text.split("~~")
                re_tokenized_text = custom_tokenize(' '.join(tokenized_text_list), boolean_synonym)
            else:
                re_tokenized_text = custom_tokenize(document.lower(), boolean_synonym)

            resume_filenames.append(candidate_id)
            resume_texts.append(re_tokenized_text)

    # HYBRID SEARCH - EXACT KEYWORD CANDIDATES
    # Preserve semantic candidates and add exact weighted-keyword
    # matches before BM25 ranking.
    print("Adding exact keyword candidates to BM25 corpus...")

    exact_where_clause = {}

    if min_experience is not None and max_experience is not None:
        exact_where_clause = {
            "$and": [
                {"years_of_experience": {"$gte": min_experience}},
                {"years_of_experience": {"$lte": max_experience}}
            ]
        }
    elif min_experience is not None:
        exact_where_clause = {
            "years_of_experience": {"$gte": min_experience}
        }
    elif max_experience is not None:
        exact_where_clause = {
            "years_of_experience": {"$lte": max_experience}
        }

    if exact_where_clause:
        exact_results = await collection.get(
            where=exact_where_clause,
            include=["documents", "metadatas"]
        )
    else:
        exact_results = await collection.get(
            include=["documents", "metadatas"]
        )

    exact_keywords = [
        keyword.lower().strip()
        for keyword, _ in keywords_with_weights
        if keyword and keyword.strip()
    ]

    # OPT: compile identical word-boundary patterns once per request.
    exact_keyword_patterns = [
        re.compile(r"\b" + re.escape(keyword) + r"\b")
        for keyword in exact_keywords
    ]

    existing_filenames = set(resume_filenames)
    exact_added = 0

    for document, metadata in zip(
        exact_results["documents"],
        exact_results["metadatas"]
    ):
        candidate_id = metadata.get("filename", "N/A")
        document_text = document or ""
        document_lower = document_text.lower()

        if candidate_id in existing_filenames:
            continue

        if any(
            pattern.search(document_lower)
            for pattern in exact_keyword_patterns
        ):
            tokenized_text = metadata.get(
                "tokenized_text",
                None
            )

            if tokenized_text:
                tokenized_text_list = tokenized_text.split("~~")

                re_tokenized_text = custom_tokenize(
                    " ".join(tokenized_text_list),
                    boolean_synonym
                )
            else:
                re_tokenized_text = custom_tokenize(
                    document_lower,
                    boolean_synonym
                )

            resume_filenames.append(candidate_id)
            resume_texts.append(re_tokenized_text)

            existing_filenames.add(candidate_id)
            exact_added += 1

    print(
        f"Exact keyword candidates added: {exact_added}"
    )

    print(
        f"Final hybrid BM25 corpus size: {len(resume_filenames)}"
    )
    if not resume_texts:
        raise ValueError("No valid tokenized texts found in metadata.")

    bm25 = BM25Okapi(resume_texts)

def parse_keywords_and_weights(keywords_with_weights):
    """
    Parses the keywords and weights provided that the developer inputs or manually sets the keywords and weights when the file is ran(uncomment out the lines asks for user input)
    """
    keywords = []
    weights = {}
    
    for item in keywords_with_weights:
        if isinstance(item, tuple) and len(item) == 2:
            keyword, weight = item
            keywords.append(keyword)
            weights[keyword] = weight
        else:
            keywords.append(item)
            weights[item] = 1  # Default weight is 1 if not specified
    
    return keywords, weights

def query_by_word(query, keywords_with_weights, boolean_synonym, top_n=200):
    """
    Takes the keywords from parsing function above and tokenizes them and applies the bm25 algorithm and ranks them by their score value for the specific keyword
    """

    keywords, _ = parse_keywords_and_weights(keywords_with_weights)
    query_tokens = custom_tokenize(query.lower(), boolean_synonym)
    scores = bm25.get_scores(query_tokens)
    ranked_results = sorted(zip(resume_filenames, scores), key=lambda x: x[1], reverse=True)
    
    # Filter out results with a score of 0.0
    filtered_results = [(filename, score) for filename, score in ranked_results if score > 0.0]
    
    return filtered_results[:200]

def compile_list_per_keyword(keywords, keywords_with_weights, boolean_synonym, top_n=200):
    """
    Compiles the output of the query_by_word function into multiple lists for each keyword
    """
    keyword_results = {}

    for keyword in keywords:
        # print(f"Processing keyword: {keyword}")
        results = query_by_word(keyword, keywords_with_weights, boolean_synonym, top_n=200)
        keyword_results[keyword] = results

    return keyword_results

def present_list(keywords_with_weights, boolean_synonym, top_n=200):
    """
    Optimized version of the present_list function using KeywordProcessor for faster keyword matching.
    """
    keywords, weights = parse_keywords_and_weights(keywords_with_weights)
    keyword_results = compile_list_per_keyword(keywords, keywords_with_weights, boolean_synonym)

    combined_results = {}
    keyword_counts = {}

    # Combine results with weighted scores
    for keyword, results in keyword_results.items():
        weight = weights[keyword]
        for filename, score in results:
            combined_results[filename] = combined_results.get(filename, 0) + score * weight

    # Sort combined results by cumulative score in descending order
    sorted_combined_results = sorted(combined_results.items(), key=lambda x: x[1], reverse=True)

    # Use KeywordProcessor for faster keyword matching
    keyword_processor = KeywordProcessor(case_sensitive=False)
    for boolean_name, synonyms in boolean_synonym.items():
        for synonym in synonyms:
            keyword_processor.add_keyword(synonym.lower(), boolean_name)

    # Calculate keyword counts for each resume
    for filename, _ in sorted_combined_results:
        resume_tokens = next((text for fname, text in zip(resume_filenames, resume_texts) if fname == filename), None)
        if resume_tokens:
            resume_text = ' '.join(resume_tokens).lower()
            matches = keyword_processor.extract_keywords(resume_text)
            keyword_counts[filename] = {boolean_name: matches.count(boolean_name) for boolean_name in boolean_synonym}
    
    # Debugging: Print top matching resumes for each keyword
    for keyword, results in keyword_results.items():
        print(f"\nTop Matching Resumes for keyword '{keyword}':")
        for rank, (filename, score) in enumerate(results, start=1):
            count = keyword_counts.get(filename, {}).get(keyword, 0)
            print(f"{rank}. {filename} (BM25 Score: {score:.2f}, Keyword Count: {count})")
    
    print("\nTop Resumes After BM25:")
    for rank, (filename, score) in enumerate(sorted_combined_results[:top_n], start=1):
        print(f"{rank}. {filename} (Cumulative Score: {score:.2f})")
        print(f"Keyword Counts: {keyword_counts[filename]})")
        print(" ")

    return sorted_combined_results[:top_n], keyword_counts

async def vector_rank_list(collection, word, pool_value, min_experience=None, max_experience=None, lambda_factor=0.05):
    """
    Utilizes the chromadb collection and applies a semantic similarity search to see which candidates match accordingly based of the query(job title) and the experience level requirements
    """
    combined_results = {}

    query_embedding = model.encode(word)

    # Conditions set in place for the range of experiece that is provided by the user(min experience or max experience or both are provided)
    where_clause = {}
    if min_experience is not None and max_experience is not None:
        where_clause = {
            "$and": [
                {"years_of_experience": {"$gte": min_experience}},
                {"years_of_experience": {"$lte": max_experience}}
            ]
        }
    elif min_experience is not None:
        where_clause = {"years_of_experience": {"$gte": min_experience}}
    elif max_experience is not None:
        where_clause = {"years_of_experience": {"$lte": max_experience}}

    if where_clause:
        results = await collection.query(
            query_embeddings=[query_embedding],
            n_results=pool_value,
            include=["distances", "metadatas"],
            where=where_clause
        )
    else:
        results = await collection.query(
            query_embeddings=[query_embedding],
            n_results=pool_value,
            include=["distances", "metadatas"]
        )

    if not results.get('metadatas'):
        print(f"No metadata found in query results for words: {word}")
        return []

    for metadata, distance in zip(results['metadatas'][0], results['distances'][0]):
        candidate_id = metadata.get('filename', 'N/A')
        years_of_experience = metadata.get('years_of_experience', 0)

        # Apply custom re-ranking adjustment formula
        adjusted_distance = max(distance - (lambda_factor * min(years_of_experience, 20)), 0)

        combined_results[candidate_id] = {
            'years_of_experience': years_of_experience,
            'adjusted_distance': adjusted_distance,
            'distance': distance
        }
    
    # Separate candidates into two groups
    group_zero = [
        (filename, data) for filename, data in combined_results.items()
        if data['adjusted_distance'] == 0
    ]
    group_non_zero = [
        (filename, data) for filename, data in combined_results.items()
        if data['adjusted_distance'] > 0
    ]

    # Sort Group 1 (adjusted_distance == 0) by years_of_experience (descending)
    group_zero_sorted = sorted(group_zero, key=lambda x: x[1]['years_of_experience'], reverse=True)

    # Sort Group 2 (adjusted_distance > 0) by adjusted_distance (ascending)
    group_non_zero_sorted = sorted(group_non_zero, key=lambda x: x[1]['adjusted_distance'])

    # Convert combined_results to a list and sort by adjusted distance (lower values = better matches)

    sorted_combined_results = group_zero_sorted + group_non_zero_sorted
    
    # For debugging purposes

    print(f"\nVector Search Results: {pool_value}")
    # for rank, (filename, data) in enumerate(sorted_combined_results, start=1):
    #     print(f"{rank}. {filename} (Experience: {data['years_of_experience']}) | (Adjusted Distance: {data['adjusted_distance']})")

    return [filename for filename, data in sorted_combined_results]

async def process_resumes(collection, compare_all_titles, keywords_with_weights, boolean_synonym, job_title, pool_value, min_experience, max_experience, top_n=50):
    """
    All the functions are conducted here and it will return the top candidates and their relevant information
    """
    lambda_factor = 0.05

    # Measure time for semantic search
    semantic_search_start_time = time.time()
    await initialize_bm25_from_chromadb(collection, compare_all_titles, job_title, keywords_with_weights, boolean_synonym, pool_value, min_experience, max_experience, lambda_factor)
    semantic_search_end_time = time.time()
    semantic_search_execution_time = semantic_search_end_time - semantic_search_start_time
    print(f"Time taken for initialize bm25 search: {semantic_search_execution_time:.2f} seconds")

    # Measure time for BM25 search
    bm25_search_start_time = time.time()
    top_candidates, keyword_counts = present_list(keywords_with_weights, boolean_synonym, top_n)
    bm25_search_end_time = time.time()
    bm25_search_execution_time = bm25_search_end_time - bm25_search_start_time
    print(f"Time taken for BM25 search: {bm25_search_execution_time:.2f} seconds")
    
    max_score = max(score for _, score in top_candidates) if top_candidates else 0

    # Map the max bm25_score to max_ref
    if max_score < 1:
        max_ref = 0.75  # Weak scores
    elif 1 <= max_score < 3:
        max_ref = 4
    elif 3 <= max_score < 6:
        max_ref = 7  # Moderate scores
    elif 6 <= max_score < 10:
        max_ref = 10  # Strong scores
    elif 10 <= max_score < 15:
        max_ref = 15  # Very strong scores
    else:
        max_ref = 20  # Exceptionally strong scores

    # print(f"Max Score: {max_score}, Mapped max_ref: {max_ref}")
    
    results = []
    for rank, (filename, score) in enumerate(top_candidates, start=1):
        # Retrieve the resume text from the collection
        result = await collection.get(where={"filename": filename}, include=["documents", "metadatas"])
        if not result['documents']:
            print(f"Resume does not contain resume text for {filename}.")
            continue

        resume_text = result['documents'][0]
        metadata = result['metadatas'][0]

        #Logithmic scaling to translate BM25 scores to Relevance Score percentages
        scaled_score = (math.log(1 + score) / math.log(1 + max_ref)) * 100

        related_words = {}
        for keyword, count in keyword_counts.get(filename, {}).items():
            # Initialize related keywords with counts, skipping the main keyword if it appears in the related keyword list
            related_keywords_with_counts = [
                {"keyword": synonym, "count": len(re.findall(r'\b' + re.escape(synonym.lower().replace(' ', '_')) + r'\b', resume_text.lower()))}
                for synonym in boolean_synonym.get(keyword, [])
                if synonym.lower() != keyword.lower()  # Skip the main keyword
            ]

            filtered_related_keywords = [
                {"keyword": synonym["keyword"], "count": synonym["count"]}
                for synonym in related_keywords_with_counts
            ]

            # Calculate the sum of related keyword counts
            related_keywords_sum = sum(synonym["count"] for synonym in filtered_related_keywords)

            # Calculate the main keyword count
            main_keyword_count = count - related_keywords_sum

            # Add the main keyword count as a related keyword
            filtered_related_keywords.append({"keyword": keyword, "count": main_keyword_count})

            # Add the filtered related keywords to the related_words dictionary
            related_words[keyword] = {
                "count": count,  # Keep the total count for the main keyword
                "related_keywords": filtered_related_keywords or []  # Ensure related_keywords is always an array
            }
        
        candidate_info = {
            "rank": rank,
            "filename": filename,
            "candidate_name": metadata.get("candidate_name", "Unknown"),
            "skills": metadata.get("core_technologies", "N/A"),
            "experience_years": metadata.get("years_of_experience", "N/A"),
            "education": metadata.get("education", "N/A"),
            "job_title": metadata.get("most_recent_job_title", "N/A"),
            "contact_email": metadata.get("email", "N/A"),
            "contact_phone": metadata.get("phone_number", "N/A"),
            "location": metadata.get("location", "N/A"),
            "relevance_score": round(scaled_score, 2),
            # "keyword_counts": keyword_counts.get(filename, {})
            "keyword_counts": related_words
        }

        results.append(candidate_info)

    return results

async def main():
    start_time = time.time()
    
    # Query by job title and whatever relevant skills for vector/similarity search 
    
    # job_title = "Data Architect/Modeller - Senior with skills in architecture, Data Architect, Data Factory, Data Modelling, Erwin, Healthcare, Integration, Lakehouse, Logical, Modeling, OPS"
    # job_title = "Training Specialist - Senior with skills in CHANGE MANAGEMENT, OPS, Instructional Design, Training, Articulate Storyline, Training Course"
    # job_title = "Product Manager - Senior with skills in Agile, Cloud, CRM, Functional, PMP, PROJECT MANAGEMENT, Public Sector, QUALITY, Stakeholder"
    job_title = "Application Support Specialist - Senior with skills in Identity & Access Management, identity, Access, IAM, OAuth 2, OAuth 2.0, OpenID, OpenID Connect, SSO, Single Sign-on, Single Sign On, Single SignOn, SAML, SAML2, SAML2.0, OIDC, Connect Protocol, Authentication Protocol, Cyber Security, CyberSecurity, Software Security, IT Security, OIAM, OIM, OAM, Identity manager, Identity Management, Access Manager, Access Management, Identity and Access Manager, Identity Access Manager, Identity Access Management, Identity & Access Manager, Automation, Automation testing, Test Automation, Automated test, AUTOMATION TEST, AUTOMATED TEST, AUTOMATION SCRIPT, AUTOMATING UI, UI AUTOMATION, QA, QUALITY ASSURANCE, TESTING, TESTER, SELENIUM, Selenium, Regression testing, Regression, QA Automation, Protractor, TEST AUTOMATION DEVELOPMENT, AUTOMATE, AUTOMATED, QE, SELENIUMWEBDRIVER, Cloud Integration, Cloud Automation, Orchestration, Cloud Network, Data, Identity, Services, Data Cleaning, Data Transforming, Joining Data, Data Standards, Data Models, Data Modelling, Data Model, Data Warehouse, Data Marts, Data Mart, Datawarehouse, Synapse, DWH, Data Analytics, Data Analytic, Data Analysis, Data Analytical, Data Specialist, Data Scientist, Platform-as-a-Service, Platform as a Service, PAAS, Power Platform, Power Apps, Power App, Power Automate, Power Pages, Power Applications, PowerPlatform, PowerApps, PowerAutomate, PowerPages, PowerApplications, Power Applications, Power Virtual Agents, Flows, SharePoint, governance, Data Quality, UPM, unified project methodology, architecture gating, Gating, ARB, review board, artefacts, architecture, SOFTWARE DEVELOPER, DEVELOPER, Programmer, Software Engineer, Software Consultant, HL7, HL 7, HL-7, FHIR, CERNER, EHR, EMR, ELECTRONIC HEALTH, ELECTRONIC MEDICAL, ELECTRONIC HEALTHCARE, EPICLIS, EPICEMR, EPICEHR, MEDITECH, MEDITECHLIS, PROVINCIAL HEALTH, PHSD, COVID, COVID19, ADDICTIONS, MENTAL HEALTH, HEALTH811, HEALTH, HEALTH 811, HEALTH-811, Health Canada, Clinical Information Solution, Physicians, Clinicians, Physician, Clinician, Medical Practitioner, SNOMED-CT, SNOMED, LOINC, Ontoserver, Freedom of Information and Protection of Privacy Act, FIPPA, Municipal Freedom of Information and Protection of Privacy Act, MFIPPA, Personal Health Information Protection Act, PHIPA, HEALTH CARE, HEALTHCARE, EHEALTH, E-HEALTH, CANCER CARE, LONG TERM CARE, LONG-TERM CARE, LONGTERM CARE, CIHI, CNO, COLLEGE OF NURSES OF ONTARIO, HOSPITAL, ONTARIO HEALTH, Cloud integration, Cloud Automation, Orchestration, Cloud Network, Data, identity, services, Identity & Access Management, Identity Management, Access Management, identity, Access, IAM, OAuth 2, OAuth 2.0, OpenID, OpenID Connect, security, cyber Security, CyberSecurity, Security architecture, privacy, IAM, Identity and Access Management, Identity Management, Access Management, Identity Access Management, Identity Access Manager, Identity & Access Management, Identity & Access Manager, token-based authentication, token based authentication, JSON Token, JWT, OIDC, OpenID, Open ID, OpenID Connect, Connect Protocol, Authentication Protocol, SAML, SAML2, SAML2.0, OAuth, OAuth 2, OAuth 2.0, Oauth2, SSO, Single Sign-on, Single Sign On, Single SignOn, Software Security, IT Security, Identity manager, Access Manager, IAA, OIM, OAM, OIAM, restAPI, Rest API, restful, RestfulAPI, restAPIs, Rest APIs, restful, RestfulAPIs, WebAPI, Web API, Microservices, Microservice, API, APIs, responsive web, MQ, Messaging queue, Messaging, KAFKA, Integration, SOAP, SOAPUI, security, cyber Security, Security architecture, privacy, IAM, Identity and Access Management, token-based authentication, OIDC, SAML, OAUTH, accessibility, TRA, PIA, Component architecture, Design pattern, OPS, MINISTRY, Public Sector, ONTARIO PUBLIC SERVICE, ONTARIO PROVINCIAL SERVICE, FEDERAL GOVERNMENT, PROVINCIAL GOVERNMENT, ONTARIO GOVERNMENT, GOVERNMENT OF ONTARIO, ONTARIO GOVT., EHEALTH, E-HEALTH, MOH, CANCER CARE, HEALTH SERVICES CLUSTER, LONG TERM CARE, LONG-TERM CARE, LONGTERM CARE, LAND AND RESOURCES, LAND & RESOURCES, LABOUR AND TRANSPORTATION, LABOUR & TRANSPORTATION, COMMUNITY SERVICES CLUSTER, LCBO, JUSTICE TECHNOLOGY SERVICES, MGCS, SERVICE ONTARIO, TREASURY BOARD, SOLGEN, DEPARTMENT OF, ALBERTA HEALTH, JUSTICE, SOLICITOR, SERVICE ALBERTA, OF TRANSPORTATION, MOT, CITY OF, Ontario Health, OntarioHealth, Ehealth Ontario, AGRICULTURE AND FOOD, ATTORNEY GENERAL, EDUCATION AND CHILD CARE, EDUCATION AND CHILDCARE, ENVIRONMENT AND CLIMATE, NATURAL RESOURCES, CBSA, CANADA BORDER SERVICES AGENCY, AGRICULTURE AND AGRI-FOOD, AUDITOR GENERAL, CANADA REVENUE AGENCY, CORRECTIONAL SERVICE, CORRECTIONAL SERVICES, security, cyber Security, Security architecture, privacy, IAM, Identity and Access Management, Identity and Access management, identity management, information governance, token-based authentication, token based authentication, OIDC, SAML, OAUTH, Oauth2, Oauth2.0, PKI, Authentication, AUTHENTICATION, AUTHENTICATOR, authorization, AUTHORIZATION, Single Sign On, SSO, Single-Sign On, Single Sign-On, Single SignOn, MFA, multi-factor authentication, multifactor authentication, multi factor authentication, Two factor authentication, Two-factor authentication, multi-factor authenticator, multifactor authenticator, multi factor authenticator, Two factor authenticator, Two-factor authenticator, security design, security mechanisms, security mechanism, security planning, accessibility, TRA, PIA, Component architecture, Design pattern, Cloud integration, Cloud Automation, Orchestration, Cloud Network, Data, identity, services, triage, manual test, Automation"

    # Range of experience for the experience years the list of candidates should have
    
    min_experience = 0
    max_experience = 60

    top_n = 25
    pool_value = 750

    compare_all_titles = True

    # Boolean Names and Weightages examples

    # boolean_query = '"architecture", "2.14" AND "Data Architect", "35.00" AND "Data Factory", "2.14" AND "Data Modelling", "35.00" AND "Erwin", "2.14" AND "Healthcare", "2.50" AND "Integration", "2.14" AND "Lakehouse", "2.14" AND "Logical", "2.14" AND "Modeling", "2.14" AND "OPS", "12.50"'
    # boolean_query = '"Training Course", "12.50" AND "Articulate Storyline", "5.83" AND "Training", "35.00" AND "Instructional Design", "35.00" AND "Public Sector", "5.83" AND "CHANGE MANAGEMENT", "5.83"'
    boolean_query = '"Access", "25.00" AND "Automation", "3.41" AND "Data", "3.41" AND "Flows", "3.41" AND "governance", "3.41" AND "Healthcare", "3.41" AND "identity", "3.41" AND "Identity Management", "3.41" AND "Integration", "25.00" AND "privacy", "3.41" AND "Public Sector", "12.50" AND "security", "3.41" AND "services", "3.41" AND "triage", "3.41"'
    # boolean_query = '"Agile", "2.92" AND "Cloud", "2.92" AND "CRM", "2.92" AND "Functional", "2.92" AND "PMP", "35.00" AND "PROJECT MANAGEMENT", "35.00" AND "Public Sector", "12.50" AND "QUALITY", "2.92" AND "Stakeholder", "2.92"'
    
    # boolean_synonym = {
    #     "Training Course": ["Training Course", "Authoring Tool", "Articulate Storyline", "Camtasia", "Vyond"],
    #     "Articulate Storyline": ["Articulate Storyline", "Camtasia", "Vyond"],
    #     "Training": ["Training", "Trainer", "Instructional Designer", "Instructional Design"],
    #     "Instructional Design": ["Instructional Design", "Instructional Designer", "PROSCI"],
    #     "Public Sector": [
    #         "OPS", "MINISTRY", "Public Sector", "ONTARIO PUBLIC SERVICE", "ONTARIO PROVINCIAL SERVICE",
    #         "FEDERAL GOVERNMENT", "PROVINCIAL GOVERNMENT", "ONTARIO GOVERNMENT", "GOVERNMENT OF ONTARIO",
    #         "ONTARIO GOVT.", "EHEALTH", "E-HEALTH", "MOH", "CANCER CARE", "HEALTH SERVICES CLUSTER",
    #         "LONG TERM CARE", "LONG-TERM CARE", "LONGTERM CARE", "LAND AND RESOURCES", "LAND & RESOURCES",
    #         "LABOUR AND TRANSPORTATION", "LABOUR & TRANSPORTATION", "COMMUNITY SERVICES CLUSTER", "LCBO",
    #         "JUSTICE TECHNOLOGY SERVICES", "MGCS", "SERVICE ONTARIO", "TREASURY BOARD", "SOLGEN",
    #         "DEPARTMENT OF", "ALBERTA HEALTH", "JUSTICE", "SOLICITOR", "SERVICE ALBERTA", "OF TRANSPORTATION",
    #         "MOT", "CITY OF", "Ontario Health", "OntarioHealth", "Ehealth Ontario", "AGRICULTURE AND FOOD",
    #         "ATTORNEY GENERAL", "EDUCATION AND CHILD CARE", "EDUCATION AND CHILDCARE", "ENVIRONMENT AND CLIMATE",
    #         "NATURAL RESOURCES", "CBSA", "CANADA BORDER SERVICES AGENCY", "AGRICULTURE AND AGRI-FOOD",
    #         "AUDITOR GENERAL", "CANADA REVENUE AGENCY", "CORRECTIONAL SERVICE", "CORRECTIONAL SERVICES"
    #     ],
    #     "CHANGE MANAGEMENT": [
    #         "CHANGE MANAGEMENT", "CHANGE REQUEST", "RFC", "REQUEST FOR CHANGE", "SERVICE MANAGEMENT",
    #         "SERVICE LEVEL MANAGEMENT", "PROBLEM MANAGEMENT", "RELEASE MANAGEMENT", "CAPACITY MANAGEMENT",
    #         "INCIDENT MANAGEMENT", "COMMUNICATION MANAGEMENT", "ORGANIZATIONAL CHANGE", "ITSM",
    #         "IT SERVICE MANAGEMENT", "INFORMATION TECHNOLOGY SERVICE MANAGEMENT", "ITIL",
    #         "INFORMATION TECHNOLOGY INFRASTRUCTURE LIBRARY", "STAKEHOLDER MANAGEMENT", "MANAGING STAKEHOLDER",
    #         "RISK MANAGEMENT", "MANAGING RISK", "MANAGING ISSUES", "ISSUE MANAGEMENT", "TIME MANAGEMENT",
    #         "MANAGING TIME", "SCOPE MANAGEMENT", "MANAGING SCOPE", "RESOURCE MANAGEMENT", "MANAGING RESOURCE"
    #     ]
    # }

    boolean_synonym = {
        "Access": [
            "Identity & Access Management", "identity", "Access", "IAM", "OAuth 2", "OAuth 2.0", "OpenID", 
            "OpenID Connect", "SSO", "Single Sign-on", "Single Sign On", "Single SignOn", "SAML", "SAML2", 
            "SAML2.0", "OIDC", "Connect Protocol", "Authentication Protocol", "Cyber Security", "CyberSecurity", 
            "Software Security", "IT Security", "OIAM", "OIM", "OAM", "Identity manager", "Identity Management", 
            "Access Manager", "Access Management", "Identity and Access Manager", "Identity Access Manager", 
            "Identity Access Management", "Identity & Access Manager"
        ],
        "Automation": [
            "Automation", "Automation testing", "Test Automation", "Automated test", "AUTOMATION TEST", 
            "AUTOMATED TEST", "AUTOMATION SCRIPT", "AUTOMATING UI", "UI AUTOMATION", "QA", "QUALITY ASSURANCE", 
            "TESTING", "TESTER", "SELENIUM", "Selenium", "Regression testing", "Regression", "QA Automation", 
            "Protractor", "TEST AUTOMATION DEVELOPMENT", "AUTOMATE", "AUTOMATED", "QE", "SELENIUMWEBDRIVER"
        ],
        "Data": [
            "Cloud Integration", "Cloud Automation", "Orchestration", "Cloud Network", "Data", "Identity", 
            "Services", "Data Cleaning", "Data Transforming", "Joining Data", "Data Standards", "Data Models", 
            "Data Modelling", "Data Model", "Data Warehouse", "Data Marts", "Data Mart", "Datawarehouse", 
            "Synapse", "DWH", "Data Analytics", "Data Analytic", "Data Analysis", "Data Analytical", 
            "Data Specialist", "Data Scientist"
        ],
        "Flows": [
            "Platform-as-a-Service", "Platform as a Service", "PAAS", "Power Platform", "Power Apps", 
            "Power App", "Power Automate", "Power Pages", "Power Applications", "PowerPlatform", "PowerApps", 
            "PowerAutomate", "PowerPages", "PowerApplications", "Power Applications", "Power Virtual Agents", 
            "Flows", "SharePoint"
        ],
        "governance": [
            "governance", "Data Quality", "UPM", "unified project methodology", "architecture gating", 
            "Gating", "ARB", "review board", "artefacts", "architecture", "SOFTWARE DEVELOPER", "DEVELOPER", 
            "Programmer", "Software Engineer", "Software Consultant"
        ],
        "Healthcare": [
            "HL7", "HL 7", "HL-7", "FHIR", "CERNER", "EHR", "EMR", "ELECTRONIC HEALTH", "ELECTRONIC MEDICAL", 
            "ELECTRONIC HEALTHCARE", "EPICLIS", "EPICEMR", "EPICEHR", "MEDITECH", "MEDITECHLIS", 
            "PROVINCIAL HEALTH", "PHSD", "COVID", "COVID19", "ADDICTIONS", "MENTAL HEALTH", "HEALTH811", 
            "HEALTH", "HEALTH 811", "HEALTH-811", "Health Canada", "Clinical Information Solution", 
            "Physicians", "Clinicians", "Physician", "Clinician", "Medical Practitioner", "SNOMED-CT", 
            "SNOMED", "LOINC", "Ontoserver", "Freedom of Information and Protection of Privacy Act", 
            "FIPPA", "Municipal Freedom of Information and Protection of Privacy Act", "MFIPPA", 
            "Personal Health Information Protection Act", "PHIPA", "HEALTH CARE", "HEALTHCARE", "EHEALTH", 
            "E-HEALTH", "CANCER CARE", "LONG TERM CARE", "LONG-TERM CARE", "LONGTERM CARE", "CIHI", "CNO", 
            "COLLEGE OF NURSES OF ONTARIO", "HOSPITAL", "ONTARIO HEALTH"
        ],
        "identity": [
            "Cloud integration", "Cloud Automation", "Orchestration", "Cloud Network", "Data", "identity", 
            "services", "Identity & Access Management", "Identity Management", "Access Management", "identity", 
            "Access", "IAM", "OAuth 2", "OAuth 2.0", "OpenID", "OpenID Connect"
        ],
        "Identity Management": [
            "security", "cyber Security", "CyberSecurity", "Security architecture", "privacy", "IAM", 
            "Identity and Access Management", "Identity Management", "Access Management", "Identity Access Management", 
            "Identity Access Manager", "Identity & Access Management", "Identity & Access Manager", 
            "token-based authentication", "token based authentication", "JSON Token", "JWT", "OIDC", "OpenID", 
            "Open ID", "OpenID Connect", "Connect Protocol", "Authentication Protocol", "SAML", "SAML2", 
            "SAML2.0", "OAuth", "OAuth 2", "OAuth 2.0", "Oauth2", "SSO", "Single Sign-on", "Single Sign On", 
            "Single SignOn", "Software Security", "IT Security", "Identity manager", "Access Manager", "IAA", 
            "OIM", "OAM", "OIAM"
        ],
        "Integration": [
            "restAPI", "Rest API", "restful", "RestfulAPI", "restAPIs", "Rest APIs", "restful", "RestfulAPIs", 
            "WebAPI", "Web API", "Microservices", "Microservice", "API", "APIs", "responsive web", "MQ", 
            "Messaging queue", "Messaging", "KAFKA", "Integration", "SOAP", "SOAPUI"
        ],
        "privacy": [
            "security", "cyber Security", "Security architecture", "privacy", "IAM", "Identity and Access Management", 
            "token-based authentication", "OIDC", "SAML", "OAUTH", "accessibility", "TRA", "PIA", 
            "Component architecture", "Design pattern"
        ],
        "Public Sector": [
            "OPS", "MINISTRY", "Public Sector", "ONTARIO PUBLIC SERVICE", "ONTARIO PROVINCIAL SERVICE", 
            "FEDERAL GOVERNMENT", "PROVINCIAL GOVERNMENT", "ONTARIO GOVERNMENT", "GOVERNMENT OF ONTARIO", 
            "ONTARIO GOVT.", "EHEALTH", "E-HEALTH", "MOH", "CANCER CARE", "HEALTH SERVICES CLUSTER", 
            "LONG TERM CARE", "LONG-TERM CARE", "LONGTERM CARE", "LAND AND RESOURCES", "LAND & RESOURCES", 
            "LABOUR AND TRANSPORTATION", "LABOUR & TRANSPORTATION", "COMMUNITY SERVICES CLUSTER", "LCBO", 
            "JUSTICE TECHNOLOGY SERVICES", "MGCS", "SERVICE ONTARIO", "TREASURY BOARD", "SOLGEN", 
            "DEPARTMENT OF", "ALBERTA HEALTH", "JUSTICE", "SOLICITOR", "SERVICE ALBERTA", "OF TRANSPORTATION", 
            "MOT", "CITY OF", "Ontario Health", "OntarioHealth", "Ehealth Ontario", "AGRICULTURE AND FOOD", 
            "ATTORNEY GENERAL", "EDUCATION AND CHILD CARE", "EDUCATION AND CHILDCARE", "ENVIRONMENT AND CLIMATE", 
            "NATURAL RESOURCES", "CBSA", "CANADA BORDER SERVICES AGENCY", "AGRICULTURE AND AGRI-FOOD", 
            "AUDITOR GENERAL", "CANADA REVENUE AGENCY", "CORRECTIONAL SERVICE", "CORRECTIONAL SERVICES"
        ],
        "security": [
            "security", "cyber Security", "Security architecture", "privacy", "IAM", "Identity and Access Management", 
            "Identity and Access management", "identity management", "information governance", 
            "token-based authentication", "token based authentication", "OIDC", "SAML", "OAUTH", "Oauth2", 
            "Oauth2.0", "PKI", "Authentication", "AUTHENTICATION", "AUTHENTICATOR", "authorization", 
            "AUTHORIZATION", "Single Sign On", "SSO", "Single-Sign On", "Single Sign-On", "Single SignOn", 
            "MFA", "multi-factor authentication", "multifactor authentication", "multi factor authentication", 
            "Two factor authentication", "Two-factor authentication", "multi-factor authenticator", 
            "multifactor authenticator", "multi factor authenticator", "Two factor authenticator", 
            "Two-factor authenticator", "security design", "security mechanisms", "security mechanism", 
            "security planning", "accessibility", "TRA", "PIA", "Component architecture", "Design pattern"
        ],
        "services": [
            "Cloud integration", "Cloud Automation", "Orchestration", "Cloud Network", "Data", "identity", "services"
        ],
        "triage": [
            "triage", "manual test", "Automation"
        ]
    }
    
    # Parse the keywords and weights from the strings above
    keywords_with_weights = [
        (kw.strip().split(',')[0].strip('" '), float(kw.strip().split(',')[1].strip('" ')) / 100)
        for kw in boolean_query.split('AND')
    ]

    collection = await initialize_chromadb_client()
    
    process_start_time = time.time()
    results = await process_resumes(collection, compare_all_titles, keywords_with_weights, boolean_synonym, job_title, pool_value, min_experience, max_experience, top_n)
    process_end_time = time.time()

    process_execution_time = process_end_time - process_start_time
    print(f"Time taken to execute process_resumes: {process_execution_time:.2f} seconds")
    
    # Debugging purposes

    # for candidate_info in results:
    #     print(f"Rank: {candidate_info['rank']}")
    #     print(f"Filename: {candidate_info['filename']}")
    #     print(f"Candidate Name: {candidate_info['candidate_name']}")
    #     print(f"Skills: {candidate_info['skills']}")
    #     print(f"Experience (Years): {candidate_info['experience_years']}")
    #     print(f"Education: {candidate_info['education']}")
    #     print(f"Job Title: {candidate_info['job_title']}")
    #     print(f"Contact Email: {candidate_info['contact_email']}")
    #     print(f"Contact Phone: {candidate_info['contact_phone']}")
    #     print(f"BM25 Relevance Score: {candidate_info['relevance_score']:.2f}")
    #     print(f"Keyword Counts: {candidate_info['keyword_counts']}")
    #     print("-" * 40)
    
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.2f} seconds")

# Prints out the output on a txt file
if __name__ == "__main__":
    with open('output2.txt', 'w') as f:
        sys.stdout = f
        asyncio.run(main())
    sys.stdout = sys.__stdout__
