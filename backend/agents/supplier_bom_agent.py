"""
Autonomous Supplier BOM Agent - Enhanced multi-sheet Excel and CSV processing
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class SupplierBOMAgent:
    def __init__(self, gemini_client):
        self.gemini_client = gemini_client
        self.stats = {"files_processed": 0, "sheets_processed": 0, "items_extracted": 0, "errors": 0}
        logger.info("Autonomous Supplier BOM Agent initialized")

    async def process_supplier_file(self, file_path: str) -> dict:
        """Process supplier BOM file directly - handles Excel/CSV autonomously"""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"Supplier file not found: {file_path}")

            file_ext = file_path_obj.suffix.lower()
            logger.info(f"Processing supplier BOM file: {file_path_obj.name}")

            if file_ext in ['.xlsx', '.xls']:
                bom_data = await self._process_excel_file(file_path)
            elif file_ext == '.csv':
                bom_data = await self._process_csv_file(file_path)
            else:
                raise ValueError(f"Unsupported supplier BOM format: {file_ext}")

            # Update statistics
            self.stats["files_processed"] += 1
            self.stats["items_extracted"] += bom_data.get("total_items", 0)

            return {
                "success": True,
                "bom_data": bom_data,
                "file_type": file_ext,
                "total_items": bom_data.get("total_items", 0),
                "total_sheets": bom_data.get("total_sheets", 0),
                "processing_stats": self.stats.copy()
            }

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Supplier BOM processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "bom_data": self._create_demo_bom_data(file_path),
                "processing_stats": self.stats.copy()
            }

    async def _process_excel_file(self, file_path: str) -> Dict:
        """Process multi-sheet Excel file autonomously"""
        try:
            excel_file = pd.ExcelFile(file_path)
            all_sheets_data = {}
            total_items = 0

            logger.info(f"Found {len(excel_file.sheet_names)} sheets in Excel file")

            for sheet_name in excel_file.sheet_names:
                logger.info(f"Processing Excel sheet: {sheet_name}")

                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    sheet_data = await self._process_dataframe(df, sheet_name)

                    if sheet_data["valid_items"] > 0:  # Only include sheets with data
                        all_sheets_data[sheet_name] = sheet_data
                        total_items += sheet_data["valid_items"]
                        self.stats["sheets_processed"] += 1
                    else:
                        logger.info(f"Skipping empty sheet: {sheet_name}")

                except Exception as e:
                    logger.warning(f"Error processing sheet {sheet_name}: {e}")
                    continue

            return {
                "file_path": file_path,
                "file_type": "excel",
                "sheets": all_sheets_data,
                "total_sheets": len(all_sheets_data),
                "total_items": total_items,
                "extraction_metadata": {
                    "sheet_names": list(all_sheets_data.keys()),
                    "processing_timestamp": pd.Timestamp.now().isoformat(),
                    "sheets_with_data": len(all_sheets_data),
                    "sheets_skipped": len(excel_file.sheet_names) - len(all_sheets_data)
                }
            }

        except Exception as e:
            logger.error(f"Error processing Excel file {file_path}: {e}")
            raise

    async def _process_csv_file(self, file_path: str) -> Dict:
        """Process CSV file autonomously"""
        try:
            df = pd.read_csv(file_path)
            sheet_data = await self._process_dataframe(df, "main")

            self.stats["sheets_processed"] += 1

            return {
                "file_path": file_path,
                "file_type": "csv",
                "sheets": {"main": sheet_data},
                "total_sheets": 1,
                "total_items": sheet_data["valid_items"],
                "extraction_metadata": {
                    "sheet_names": ["main"],
                    "processing_timestamp": pd.Timestamp.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error processing CSV file {file_path}: {e}")
            raise

    async def _process_dataframe(self, df: pd.DataFrame, sheet_name: str) -> Dict:
        """Process DataFrame with intelligent column detection"""
        # Clean dataframe
        df = df.dropna(how='all')  # Remove empty rows
        df = df.fillna('')  # Fill NaN with empty strings

        if df.empty:
            logger.warning(f"Sheet {sheet_name} is empty after cleaning")
            return {
                "sheet_name": sheet_name,
                "items": [],
                "column_mapping": {},
                "total_rows": 0,
                "valid_items": 0,
                "columns_detected": []
            }

        # Detect column mappings using AI or heuristics
        column_mapping = await self._detect_columns(df.columns.tolist(), df.head(3).to_dict('records'))

        # Extract items
        items = []
        for idx, row in df.iterrows():
            item = self._extract_item_from_row(row, column_mapping, idx)
            if item and self._is_valid_bom_item(item):
                items.append(item)

        return {
            "sheet_name": sheet_name,
            "items": items,
            "column_mapping": column_mapping,
            "total_rows": len(df),
            "valid_items": len(items),
            "columns_detected": df.columns.tolist(),
            "extraction_quality": len(items) / len(df) if len(df) > 0 else 0
        }

    async def _detect_columns(self, columns: List[str], sample_rows: List[Dict]) -> Dict[str, str]:
        """Use AI to detect column mappings or fallback to heuristics"""
        if self.gemini_client and self.gemini_client.is_available():
            try:
                return await self._ai_column_detection(columns, sample_rows)
            except Exception as e:
                logger.warning(f"AI column detection failed: {e}, using heuristic fallback")

        return self._heuristic_column_detection(columns)

    async def _ai_column_detection(self, columns: List[str], sample_rows: List[Dict]) -> Dict[str, str]:
        """Use AI to identify column mappings"""
        column_analysis_prompt = f"""Analyze these Excel/CSV columns and sample data to identify BOM fields.

        Columns: {columns}
        Sample data: {sample_rows}

        Map columns to these standard BOM fields:
        - part_number: Part/item numbers or codes
        - description: Item descriptions or names
        - category: Product categories or types
        - manufacturer: Manufacturer or supplier names  
        - quantity: Quantities or counts
        - unit_price: Individual item prices
        - total_price: Total prices or amounts
        - specifications: Technical specs or details

        Return only valid mappings as JSON:
        {{"part_number": "actual_column_name", "description": "actual_column_name"}}"""

        response = await self.gemini_client.generate_content(
            column_analysis_prompt,
            temperature=0.1,
            max_tokens=800
        )

        # Parse AI response
        import json
        response_cleaned = response.strip()
        if response_cleaned.startswith("```json"):
            response_cleaned = response_cleaned[7:-3]
        elif response_cleaned.startswith("```"):
            response_cleaned = response_cleaned[3:-3]

        return json.loads(response_cleaned)

    def _heuristic_column_detection(self, columns: List[str]) -> Dict[str, str]:
        """Fallback heuristic column detection"""
        mapping = {}
        columns_lower = [col.lower() for col in columns]

        field_keywords = {
            "part_number": ["part", "number", "pn", "item", "code", "sku", "id"],
            "description": ["description", "desc", "name", "title", "detail", "item"],
            "category": ["category", "type", "class", "group", "family"],
            "manufacturer": ["manufacturer", "mfr", "brand", "supplier", "vendor", "make"],
            "quantity": ["quantity", "qty", "count", "amount", "qnt", "stock"],
            "unit_price": ["price", "cost", "unit_price", "unit_cost", "rate", "each"],
            "total_price": ["total", "total_price", "total_cost", "amount", "value"],
            "specifications": ["spec", "specification", "specs", "details", "notes", "comments"]
        }

        for field, keywords in field_keywords.items():
            for i, col_lower in enumerate(columns_lower):
                if any(keyword in col_lower for keyword in keywords):
                    mapping[field] = columns[i]
                    break

        return mapping

    def _extract_item_from_row(self, row: pd.Series, column_mapping: Dict[str, str], row_index: int) -> Optional[Dict]:
        """Extract BOM item from DataFrame row"""
        try:
            item = {
                "row_index": row_index,
                "raw_data": row.to_dict()
            }

            # Map standard fields
            for field, column_name in column_mapping.items():
                if column_name and column_name in row.index:
                    value = row[column_name]
                    if pd.notna(value) and str(value).strip():
                        item[field] = str(value).strip()
                    else:
                        item[field] = ""
                else:
                    item[field] = ""

            return item

        except Exception as e:
            logger.warning(f"Error extracting item from row {row_index}: {e}")
            return None

    def _is_valid_bom_item(self, item: Dict) -> bool:
        """Check if extracted item has meaningful BOM data"""
        part_number = item.get("part_number", "").strip()
        description = item.get("description", "").strip()

        # Valid if has part number OR meaningful description
        return len(part_number) > 0 or len(description) > 3

    def _create_demo_bom_data(self, file_path: str) -> Dict:
        """Create demo BOM data when processing fails"""
        demo_items = [
            {
                "part_number": "BOLT-M6-20-SS",
                "description": "M6x20mm Stainless Steel Hex Head Bolt",
                "category": "Hardware",
                "manufacturer": "FastenerCorp",
                "quantity": "100",
                "unit_price": "0.25",
                "total_price": "25.00",
                "specifications": "Grade A2, DIN 912",
                "row_index": 1
            }
        ]

        return {
            "file_path": file_path,
            "file_type": "demo",
            "sheets": {
                "demo": {
                    "sheet_name": "demo",
                    "items": demo_items,
                    "column_mapping": {},
                    "total_rows": len(demo_items),
                    "valid_items": len(demo_items)
                }
            },
            "total_sheets": 1,
            "total_items": len(demo_items),
            "extraction_metadata": {
                "note": "Demo data - actual processing failed",
                "processing_timestamp": pd.Timestamp.now().isoformat()
            }
        }

    def get_stats(self) -> Dict:
        """Get processing statistics"""
        return self.stats.copy()
