"""
Data models for Stockbit Stream data
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd


@dataclass
class StreamComment:
    """Data model for a single stream comment/post"""
    
    username: str
    comment_text: str = ""
    timestamp: Optional[datetime] = None
    likes: int = 0
    replies: int = 0
    post_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert datetime to string for serialization
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamComment':
        """Create instance from dictionary"""
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class StreamDataManager:
    """Manager class for handling stream data collection and export"""
    
    def __init__(self):
        self.comments: List[StreamComment] = []
    
    def add_comment(self, comment: StreamComment):
        """Add a comment to the collection"""
        self.comments.append(comment)
    
    def add_comments(self, comments: List[StreamComment]):
        """Add multiple comments to the collection"""
        self.comments.extend(comments)
    
    def get_comments_count(self) -> int:
        """Get total number of comments collected"""
        return len(self.comments)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert comments to pandas DataFrame"""
        if not self.comments:
            return pd.DataFrame()
        
        data = [comment.to_dict() for comment in self.comments]
        df = pd.DataFrame(data)
        
        # Reorder columns for better readability
        column_order = [
            'username', 'timestamp', 'comment_text', 
            'likes', 'replies', 'post_id'
        ]
        
        # Only include columns that exist in the dataframe
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]
        
        return df
    
    def save_to_csv(self, filename: str) -> str:
        """Save comments to CSV file"""
        df = self.to_dataframe()
        if df.empty:
            raise ValueError("No data to save")
        
        df.to_csv(filename, index=False, encoding='utf-8')
        return filename
    
    def save_to_json(self, filename: str) -> str:
        """Save comments to JSON file"""
        if not self.comments:
            raise ValueError("No data to save")
        
        import json
        data = [comment.to_dict() for comment in self.comments]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the collected data"""
        if not self.comments:
            return {"total_comments": 0}
        
        df = self.to_dataframe()
        
        summary = {
            "total_comments": len(self.comments),
            "unique_users": df['username'].nunique() if 'username' in df.columns else 0,
            "total_likes": df['likes'].sum() if 'likes' in df.columns else 0,
            "total_replies": df['replies'].sum() if 'replies' in df.columns else 0,
            "date_range": {
                "earliest": df['timestamp'].min().isoformat() if 'timestamp' in df.columns and not df['timestamp'].isna().all() else None,
                "latest": df['timestamp'].max().isoformat() if 'timestamp' in df.columns and not df['timestamp'].isna().all() else None
            }
        }
        
        return summary