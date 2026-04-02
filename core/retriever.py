"""
University Data Retriever for UniUs Chatbot.
Loads CSV data and performs fuzzy search to find relevant university information.
"""

import pandas as pd
from rapidfuzz import fuzz, process

# Common university abbreviations → full names
ABBREVIATIONS = {
    "mit": "massachusetts institute of technology",
    "ucla": "university of california los angeles",
    "usc": "university of southern california",
    "nyu": "new york university",
    "uc berkeley": "university of california berkeley",
    "caltech": "california institute of technology",
    "georgia tech": "georgia institute of technology",
    "ut austin": "university of texas at austin",
    "umich": "university of michigan",
    "upenn": "university of pennsylvania",
    "unc": "university of north carolina",
    "osu": "ohio state university",
    "psu": "penn state university",
    "asu": "arizona state university",
    "uva": "university of virginia",
    "uf": "university of florida",
    "bu": "boston university",
    "bc": "boston college",
    "cmu": "carnegie mellon university",
    "jhu": "johns hopkins university",
    "rpi": "rensselaer polytechnic institute",
    "vt": "virginia tech",
    "tamu": "texas a&m university",
    "lsu": "louisiana state university",
    "uiuc": "university of illinois urbana-champaign",
    "ucsd": "university of california san diego",
    "ucsb": "university of california santa barbara",
    "uci": "university of california irvine",
    "ucd": "university of california davis",
    "ucsc": "university of california santa cruz",
    "ucr": "university of california riverside",
    "gmu": "george mason university",
    "gwu": "george washington university",
    "fsu": "florida state university",
    "fiu": "florida international university",
    "usf": "university of south florida",
    "uw": "university of washington",
    "wsu": "washington state university",
    "cu boulder": "university of colorado boulder",
    "isu": "iowa state university",
    "msu": "michigan state university",
    "ou": "university of oklahoma",
    "ku": "university of kansas",
    "uk": "university of kentucky",
    "vanderbilt": "vanderbilt university",
    "emory": "emory university",
    "duke": "duke university",
    "rice": "rice university",
    "harvard": "harvard university",
    "yale": "yale university",
    "princeton": "princeton university",
    "columbia": "columbia university",
    "cornell": "cornell university",
    "stanford": "stanford university",
    "dartmouth": "dartmouth college",
    "brown": "brown university",
    "notre dame": "university of notre dame",
    "georgetown": "georgetown university",
    "tulane": "tulane university",
    "purdue": "purdue university",
    "rutgers": "rutgers university",
    "rit": "rochester institute of technology",
    "drexel": "drexel university",
    "villanova": "villanova university",
    "smu": "southern methodist university",
    "tcu": "texas christian university",
    "byu": "brigham young university",
    "ole miss": "university of mississippi",
    "clemson": "clemson university",
    "bama": "university of alabama",
    "auburn": "auburn university",
}


class UniversityRetriever:
    """Retrieves university data from CSV using fuzzy matching."""
    
    def __init__(self, csv_path: str):
        """Load the university dataset."""
        self.df = pd.read_csv(csv_path, dtype=str)
        self.df = self.df.fillna("N/A")
        
        # Pre-compute lowercase names for faster matching
        self.names = self.df["Institute_Name"].tolist()
        self.names_lower = [n.lower() for n in self.names]
        
        # Build state lookup
        self.states = self.df["State"].unique().tolist()
        self.states_lower = [s.lower() for s in self.states]
        
        # Build city lookup
        self.cities = self.df["City"].unique().tolist()
        
        # Build type lookup
        self.types = self.df["university_type"].unique().tolist()
        
        print(f"[UniUs] Loaded {len(self.df)} institutions from dataset.")
    
    def _expand_query(self, query: str) -> str:
        """Expand common abbreviations in the query."""
        q = query.lower().strip()
        # Check for exact abbreviation match
        if q in ABBREVIATIONS:
            return ABBREVIATIONS[q]
        # Check if abbreviation appears in query
        for abbr, full_name in ABBREVIATIONS.items():
            if abbr in q.split():
                q = q.replace(abbr, full_name)
                break
        return q
    
    def search_by_name(self, query: str, limit: int = 5) -> list:
        """
        Fuzzy search for universities by name.
        
        Returns list of dicts with university data.
        """
        expanded = self._expand_query(query)
        
        # Use WRatio for better overall matching
        results = process.extract(
            expanded,
            self.names_lower,
            scorer=fuzz.WRatio,
            limit=limit * 2,  # Get extra results to re-rank
            score_cutoff=50
        )
        
        # Also try token_sort_ratio for word-reordered matches
        results2 = process.extract(
            expanded,
            self.names_lower,
            scorer=fuzz.token_sort_ratio,
            limit=limit,
            score_cutoff=55
        )
        
        # Merge and deduplicate, keeping best score
        seen = {}
        for match_text, score, index in (results or []) + (results2 or []):
            if index not in seen or score > seen[index][1]:
                seen[index] = (match_text, score, index)
        
        # Sort by score descending and take top `limit`
        merged = sorted(seen.values(), key=lambda x: x[1], reverse=True)[:limit]
        
        if not merged:
            return []
        
        matches = []
        for match_text, score, index in merged:
            row = self.df.iloc[index]
            matches.append({
                "name": row["Institute_Name"],
                "city": row["City"],
                "state": row["State"],
                "state_abbr": row["State_Abbrevation"],
                "type": row["university_type"],
                "address": row["Address"],
                "zip": row["ZipCode"],
                "chief_name": row["Chief_Name"],
                "chief_title": row["Chief_Title"],
                "website": row["Web_Address"],
                "rank_global": row["rank_global"],
                "rank_us": row["rank_US"],
                "match_score": score,
            })
        
        return matches
    
    def search_by_state(self, state: str, limit: int = 10) -> list:
        """Search for universities in a specific state."""
        # Try matching full state name
        state_match = process.extractOne(
            state.lower(),
            self.states_lower,
            scorer=fuzz.ratio,
            score_cutoff=70
        )
        
        if not state_match:
            return []
        
        matched_state = self.states[state_match[2]]
        filtered = self.df[self.df["State"] == matched_state]
        
        # Prefer ranked ones first, then alphabetical
        results = []
        for _, row in filtered.head(limit).iterrows():
            results.append({
                "name": row["Institute_Name"],
                "city": row["City"],
                "state": row["State"],
                "state_abbr": row["State_Abbrevation"],
                "type": row["university_type"],
                "website": row["Web_Address"],
                "rank_global": row["rank_global"],
                "rank_us": row["rank_US"],
            })
        
        return results
    
    def search_by_type(self, uni_type: str, state: str = None, limit: int = 10) -> list:
        """Search universities by type (Public, Private, etc.)."""
        filtered = self.df
        
        # Filter by type
        type_lower = uni_type.lower()
        if "public" in type_lower:
            filtered = filtered[filtered["university_type"] == "Public"]
        elif "private" in type_lower and "non" in type_lower:
            filtered = filtered[filtered["university_type"] == "Private Non-Profit"]
        elif "private" in type_lower and "profit" in type_lower:
            filtered = filtered[filtered["university_type"] == "Private For-Profit"]
        elif "private" in type_lower:
            filtered = filtered[filtered["university_type"].str.contains("Private", case=False, na=False)]
        
        # Optionally filter by state
        if state:
            state_match = process.extractOne(
                state.lower(), self.states_lower,
                scorer=fuzz.ratio, score_cutoff=70
            )
            if state_match:
                matched_state = self.states[state_match[2]]
                filtered = filtered[filtered["State"] == matched_state]
        
        results = []
        for _, row in filtered.head(limit).iterrows():
            results.append({
                "name": row["Institute_Name"],
                "city": row["City"],
                "state": row["State"],
                "type": row["university_type"],
                "website": row["Web_Address"],
            })
        
        return results
    
    def get_stats(self) -> dict:
        """Get general dataset statistics."""
        return {
            "total_institutions": len(self.df),
            "total_states": self.df["State"].nunique(),
            "public_count": len(self.df[self.df["university_type"] == "Public"]),
            "private_nonprofit_count": len(self.df[self.df["university_type"] == "Private Non-Profit"]),
            "private_forprofit_count": len(self.df[self.df["university_type"] == "Private For-Profit"]),
            "ranked_global": len(self.df[self.df["rank_global"] != "Not Ranked"]),
            "ranked_us": len(self.df[self.df["rank_US"] != "Not Ranked"]),
        }
    
    def search(self, query: str) -> str:
        """
        Main search method. Analyzes the query and retrieves relevant context.
        Returns a formatted string of university data for the LLM.
        """
        query_lower = query.lower()
        context_parts = []
        
        # Detect if asking about a specific state
        state_mentioned = None
        for i, state in enumerate(self.states_lower):
            if state in query_lower and len(state) > 3:  # Avoid short false matches
                state_mentioned = self.states[i]
                break
        
        # Detect if asking about university type
        type_filter = None
        if "public" in query_lower:
            type_filter = "public"
        elif "private" in query_lower:
            if "non-profit" in query_lower or "nonprofit" in query_lower:
                type_filter = "private non-profit"
            elif "for-profit" in query_lower or "for profit" in query_lower:
                type_filter = "private for-profit"
            else:
                type_filter = "private"
        
        # Detect comparison queries
        comparison_words = ["compare", "vs", "versus", "difference", "between"]
        is_comparison = any(w in query_lower for w in comparison_words)
        
        # Detect stats/count queries
        stats_words = ["how many", "total", "count", "number of", "statistics", "stats"]
        is_stats = any(w in query_lower for w in stats_words)
        
        # Provide stats if requested
        if is_stats:
            stats = self.get_stats()
            context_parts.append(
                f"Dataset Statistics:\n"
                f"- Total institutions: {stats['total_institutions']}\n"
                f"- States/territories covered: {stats['total_states']}\n"
                f"- Public institutions: {stats['public_count']}\n"
                f"- Private Non-Profit: {stats['private_nonprofit_count']}\n"
                f"- Private For-Profit: {stats['private_forprofit_count']}\n"
                f"- Globally ranked: {stats['ranked_global']}\n"
                f"- US ranked: {stats['ranked_us']}"
            )
        
        # Search by name (always try this)
        name_results = self.search_by_name(query, limit=5)
        if name_results:
            for uni in name_results:
                if uni["match_score"] >= 55:
                    entry = (
                        f"\nInstitution: {uni['name']}\n"
                        f"  Location: {uni['city']}, {uni['state']} ({uni['state_abbr']})\n"
                        f"  Address: {uni['address']}, {uni['zip']}\n"
                        f"  Type: {uni['type']}\n"
                        f"  Leadership: {uni['chief_name']} ({uni['chief_title']})\n"
                        f"  Website: {uni['website']}\n"
                        f"  Global Ranking: {uni['rank_global']}\n"
                        f"  US Ranking: {uni['rank_us']}\n"
                        f"  (Match confidence: {uni['match_score']}%)"
                    )
                    context_parts.append(entry)
        
        # Search by state if mentioned
        if state_mentioned:
            state_results = self.search_by_state(state_mentioned, limit=8)
            if state_results:
                state_info = f"\nInstitutions in {state_mentioned} (showing up to 8):\n"
                for uni in state_results:
                    state_info += f"  - {uni['name']} ({uni['type']}) in {uni['city']}\n"
                context_parts.append(state_info)
        
        # Search by type if mentioned
        if type_filter:
            type_results = self.search_by_type(
                type_filter, 
                state=state_mentioned,
                limit=8
            )
            if type_results:
                type_info = f"\n{type_filter.title()} institutions"
                if state_mentioned:
                    type_info += f" in {state_mentioned}"
                type_info += " (showing up to 8):\n"
                for uni in type_results:
                    type_info += f"  - {uni['name']} in {uni['city']}, {uni['state']}\n"
                context_parts.append(type_info)
        
        if not context_parts:
            return "No matching university data found in the database for this query."
        
        return "\n".join(context_parts)
