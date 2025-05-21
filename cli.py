import argparse
import sys
import os
import torch
import clip
from PIL import Image

from database import Database
from file_manager import FileManager
from tagging import TagManager
from search import SearchEngine
from gui import (
    auto_tag_image,
    get_file_type_tag,
    analyze_text_content,
    analyze_code_content,
    FILE_TYPE_MAPPINGS,
    CODE_PATTERNS,
    THEME_KEYWORDS
)

def main_cli():
    parser = argparse.ArgumentParser(
        description="Digital Library Management System CLI"
    )

    subparsers = parser.add_subparsers(dest="command")

    # ---- file commands ----
    parser_add_file = subparsers.add_parser("add-file", help="Add a new file")
    parser_add_file.add_argument("file_path", help="Path to the file")
    parser_add_file.add_argument("--metadata", help="Optional metadata", default="")
    parser_add_file.add_argument("--no-auto-tag", action="store_true", help="Disable automatic tagging")

    parser_remove_file = subparsers.add_parser("remove-file", help="Remove a file by ID")
    parser_remove_file.add_argument("file_id", type=int)

    parser_list_files = subparsers.add_parser("list-files", help="List all files")
    parser_list_files.add_argument("--show-tags", action="store_true", help="Show tags for each file")

    # ---- tag commands ----
    parser_create_tag = subparsers.add_parser("create-tag", help="Create a new tag")
    parser_create_tag.add_argument("name", help="Tag name")
    parser_create_tag.add_argument("type", help="Tag type (boolean, numeric, or string)")

    parser_delete_tag = subparsers.add_parser("delete-tag", help="Delete a tag by ID")
    parser_delete_tag.add_argument("tag_id", type=int)

    parser_assign_tag = subparsers.add_parser("assign-tag", help="Assign a tag to a file")
    parser_assign_tag.add_argument("file_id", type=int)
    parser_assign_tag.add_argument("tag_id", type=int)
    parser_assign_tag.add_argument("--value", help="Optional value for the tag", default=None)

    parser_remove_tag = subparsers.add_parser("remove-tag", help="Remove a tag from a file")
    parser_remove_tag.add_argument("file_id", type=int)
    parser_remove_tag.add_argument("tag_id", type=int)

    # ---- search commands ----
    parser_search = subparsers.add_parser("search", help="Search across all fields")
    parser_search.add_argument("query", help="Search query")

    parser_search_filename = subparsers.add_parser("search-filename", help="Search by filename substring")
    parser_search_filename.add_argument("query", help="Substring to look for in filenames")

    parser_search_tag = subparsers.add_parser("search-tag", help="Search by tag name")
    parser_search_tag.add_argument("tag_name")

    parser_search_tag_value = subparsers.add_parser("search-tag-value", help="Search by tag name and value")
    parser_search_tag_value.add_argument("tag_name")
    parser_search_tag_value.add_argument("value")

    # ---- auto-tag commands ----
    parser_auto_tag = subparsers.add_parser("auto-tag", help="Auto-tag a file")
    parser_auto_tag.add_argument("file_id", type=int)
    parser_auto_tag.add_argument("--type", action="store_true", help="Tag based on file type")
    parser_auto_tag.add_argument("--content", action="store_true", help="Analyze content for tags")
    parser_auto_tag.add_argument("--image", action="store_true", help="Use CLIP for image analysis")

    args = parser.parse_args()

    # Database initialization
    db = Database("library.db")
    db.connect()
    db.init_schema()

    file_mgr = FileManager(db)
    tag_mgr = TagManager(db)
    search_engine = SearchEngine(db)

    if args.command == "add-file":
        file_id = file_mgr.add_file(args.file_path, args.metadata)
        print(f"File added with ID={file_id}")

        if not args.no_auto_tag:
            # Auto-tag based on file type
            file_type_tag = get_file_type_tag(args.file_path)
            if file_type_tag:
                tag_id = tag_mgr.create_tag("file_type", "string")
                tag_mgr.assign_tag_to_file(file_id, tag_id, file_type_tag)
                print(f"Added file type tag: {file_type_tag}")

            # If it's an image, do CLIP tagging
            if args.file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')):
                try:
                    image_tag = auto_tag_image(args.file_path)
                    tag_id = tag_mgr.create_tag("auto", "string")
                    tag_mgr.assign_tag_to_file(file_id, tag_id, image_tag)
                    print(f"Added image tag: {image_tag}")
                except Exception as e:
                    print(f"Error during image analysis: {e}")

            # If it's a text or code file, analyze content
            _, ext = os.path.splitext(args.file_path)
            if ext.lower() in ['.txt', '.md', '.markdown', '.doc', '.docx', '.odt', '.rtf', 
                             '.py', '.pyw', '.ipynb', '.js', '.jsx', '.ts', '.tsx']:
                try:
                    with open(args.file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if ext.lower() in ['.txt', '.md', '.markdown', '.doc', '.docx', '.odt', '.rtf']:
                        theme_tags = analyze_text_content(content)
                        if theme_tags:
                            tag_id = tag_mgr.create_tag("content_analysis", "string")
                            for tag in theme_tags:
                                tag_mgr.assign_tag_to_file(file_id, tag_id, tag)
                            print(f"Added content tags: {', '.join(theme_tags)}")
                    
                    elif ext.lower() in ['.py', '.pyw', '.ipynb', '.js', '.jsx', '.ts', '.tsx']:
                        library_tags = analyze_code_content(content, ext)
                        if library_tags:
                            tag_id = tag_mgr.create_tag("content_analysis", "string")
                            for tag in library_tags:
                                tag_mgr.assign_tag_to_file(file_id, tag_id, tag)
                            print(f"Added library tags: {', '.join(library_tags)}")
                except Exception as e:
                    print(f"Error during content analysis: {e}")

    elif args.command == "remove-file":
        file_mgr.remove_file(args.file_id)
        print(f"File with ID={args.file_id} removed.")

    elif args.command == "list-files":
        files = file_mgr.list_files()
        for file_id, name, path, metadata in files:
            print(f"ID: {file_id}")
            print(f"Name: {name}")
            print(f"Path: {path}")
            if metadata:
                print(f"Description: {metadata}")
            
            if args.show_tags:
                tags = tag_mgr.get_tags_for_file(file_id)
                if tags:
                    print("Tags:")
                    for tag_id, tag_name, tag_type, tag_value in tags:
                        print(f"  - {tag_name}: {tag_value}")
            print("-" * 50)

    elif args.command == "create-tag":
        tag_id = tag_mgr.create_tag(args.name, args.type)
        print(f"Tag created with ID={tag_id}")

    elif args.command == "delete-tag":
        tag_mgr.delete_tag(args.tag_id)
        print(f"Tag with ID={args.tag_id} deleted.")

    elif args.command == "assign-tag":
        tag_mgr.assign_tag_to_file(args.file_id, args.tag_id, args.value)
        print(f"Tag {args.tag_id} assigned to file {args.file_id}")

    elif args.command == "remove-tag":
        tag_mgr.remove_tag_from_file(args.file_id, args.tag_id)
        print(f"Tag {args.tag_id} removed from file {args.file_id}")

    elif args.command == "search":
        results = search_engine.search_all(args.query)
        for res in results:
            print(res)

    elif args.command == "search-filename":
        results = search_engine.search_by_filename(args.query)
        for res in results:
            print(res)

    elif args.command == "search-tag":
        results = search_engine.search_by_tag_name(args.tag_name)
        for res in results:
            print(res)

    elif args.command == "search-tag-value":
        results = search_engine.search_by_tag_value(args.tag_name, args.value)
        for res in results:
            print(res)

    elif args.command == "auto-tag":
        file_info = file_mgr.get_file(args.file_id)
        if not file_info:
            print(f"File with ID={args.file_id} not found")
            return

        file_path = file_info[2]  # path is the third element

        if args.type or not (args.content or args.image):
            file_type_tag = get_file_type_tag(file_path)
            if file_type_tag:
                tag_id = tag_mgr.create_tag("file_type", "string")
                tag_mgr.assign_tag_to_file(args.file_id, tag_id, file_type_tag)
                print(f"Added file type tag: {file_type_tag}")

        if args.image or not (args.type or args.content):
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')):
                try:
                    image_tag = auto_tag_image(file_path)
                    tag_id = tag_mgr.create_tag("auto", "string")
                    tag_mgr.assign_tag_to_file(args.file_id, tag_id, image_tag)
                    print(f"Added image tag: {image_tag}")
                except Exception as e:
                    print(f"Error during image analysis: {e}")

        if args.content or not (args.type or args.image):
            _, ext = os.path.splitext(file_path)
            if ext.lower() in ['.txt', '.md', '.markdown', '.doc', '.docx', '.odt', '.rtf', 
                             '.py', '.pyw', '.ipynb', '.js', '.jsx', '.ts', '.tsx']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if ext.lower() in ['.txt', '.md', '.markdown', '.doc', '.docx', '.odt', '.rtf']:
                        theme_tags = analyze_text_content(content)
                        if theme_tags:
                            tag_id = tag_mgr.create_tag("content_analysis", "string")
                            for tag in theme_tags:
                                tag_mgr.assign_tag_to_file(args.file_id, tag_id, tag)
                            print(f"Added content tags: {', '.join(theme_tags)}")
                    
                    elif ext.lower() in ['.py', '.pyw', '.ipynb', '.js', '.jsx', '.ts', '.tsx']:
                        library_tags = analyze_code_content(content, ext)
                        if library_tags:
                            tag_id = tag_mgr.create_tag("content_analysis", "string")
                            for tag in library_tags:
                                tag_mgr.assign_tag_to_file(args.file_id, tag_id, tag)
                            print(f"Added library tags: {', '.join(library_tags)}")
                except Exception as e:
                    print(f"Error during content analysis: {e}")

    else:
        parser.print_help()

    db.close()

if __name__ == "__main__":
    main_cli()
