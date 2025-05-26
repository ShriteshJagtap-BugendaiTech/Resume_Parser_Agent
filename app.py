import streamlit as st
from supervisor_main import SupervisorAgent
import json
import os
import pandas as pd
import base64
import urllib.parse
import shutil
# Initialize SupervisorAgent
import os
os.environ["STREAMLIT_WATCH_USE_POLLING"] = "true"

os.environ['GROQ_API_KEY'] = st.secrets["GROQ_API_KEY"]

username1 = st.secrets["USERNAME"]
password1= st.secrets["PASSWORD"]


# --- Authentication Function ---
def check_password():
    def login_form():
        with st.form("login_form", clear_on_submit=False):
            st.markdown("### 🔐 Please log in")
            username = st.text_input("👤 Username", key="username")
            password = st.text_input("🔑 Password", type="password", key="password")
            submit = st.form_submit_button("Login")

            if submit:
                if username == username1 and password == password1:
                    st.session_state.authenticated = True
                    st.success("Logged in successfully! 🎉")
                    st.rerun()
                else:
                    st.error("Invalid username or password. Please try again.")

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        # Center the form using layout
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("https://cdn-icons-png.flaticon.com/512/3064/3064197.png", width=100)
            st.markdown("<h1 style='text-align: center;'>Welcome to Resume Parser Login Page</h1>", unsafe_allow_html=True)
            login_form()
        st.stop()

# --- Call login check at the top ---
check_password()

folders=["converted","resumes"]
for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)
    else:
        # Remove existing contents
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)



agent = SupervisorAgent()
# Initialize session state to handle page navigation
if "page" not in st.session_state:
    st.session_state.page = "main"

# Page configuration
# st.set_page_config(layout="wide",initial_sidebar_state="collapsed")
st.set_page_config(page_title="Resume Parser Tool", layout="wide", page_icon="data:image/jpeg;base64,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")

if "files" not in st.session_state:
    st.session_state.files = []

if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_response" not in st.session_state:
    st.session_state.pending_response = False

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "pdf_to_view" not in st.session_state:
    st.session_state.pdf_to_view = None




def render_logo_top_left():
    st.markdown("""
        <style>
            .glassy-header {
                margin-top: 30px;
                padding: 40px;
                background: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 16px;
                box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                text-align: center;
            }

            .glassy-header img {
                width: 250px;
                border-radius: 12px;
                margin-bottom: 10px;
            }

            .glassy-header h1 {
                font-size: 3rem;
                font-weight: 700;
                margin: 0;
                color: white;
                text-shadow: 0px 2px 4px rgba(0, 0, 0, 0.5);
            }
        </style>

        <div class="glassy-header">
            <img src="data:image/png;base64,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" alt="Logo">
            <h1>Resume Parser</h1>
        </div>
    """, unsafe_allow_html=True)




st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
        }
        body {
            background-color: black;
            color: white;
        }
        .top-header {
            margin-top: 20px;
            margin-bottom: 30px;
            padding: 10px 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .logo-button {
            background-color: #4a90e2;
            color: white;
            padding: 8px 20px;
            border-radius: 5px;
            border: none;
            font-weight: bold;
            cursor: default;
        }
        .section-container {
            background-color: #4a90e2;
            border: 2px solid white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .orange-box {
            background-color: orange;
            padding: 10px;
            border-radius: 5px;
            color: black;
            font-weight: bold;
            text-align: center;
            margin-bottom: 15px;
        }
        /* Hide the sidebar */
        [data-testid="stSidebar"] {
            display: none;
        }
        /* Expand main content to full width */
        .main {
            margin-left: 0 !important;
        }
    </style>
""", unsafe_allow_html=True)





if st.session_state.page == "main":
    
 
    st.markdown('</div>', unsafe_allow_html=True)
    render_logo_top_left()
    st.markdown('</div>', unsafe_allow_html=True)
    
    left_col, right_col = st.columns([2, 3])

    with left_col:
        st.markdown('<div class="orange-box">Upload Resumes</div>', unsafe_allow_html=True)
        with st.container(height=160):
            # uploaded_file = st.file_uploader("Upload Resumes", type=["pdf", "docx"], label_visibility="collapsed", accept_multiple_files=True)
            uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx", "png", "jpg", "jpeg","ppt","pptx"],accept_multiple_files=True, label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
        if uploaded_file:
            st.session_state.files = [
                {
                    "name": file.name,
                    "type": file.type,
                    "content": file.read()
                }
                for file in uploaded_file
            ]
            st.markdown('<div class="orange-box">Chat Mode</div>', unsafe_allow_html=True)
        if st.session_state.files:
            with st.container(height=100):
                
                available_modes = ["Full Compare"]
                if len(st.session_state.files) <= 3:
                    available_modes.insert(0, "Quick Compare")
                
                total_cols = len(available_modes) + 2  
                cols = st.columns(total_cols)
                # Display buttons instead of dropdown
                selected_mode = None
                #cols = st.columns(len(available_modes))
                for idx, mode in enumerate(available_modes):
                    if cols[idx + 1].button(mode):
                        selected_mode = mode

    # Update session state based on selected mode
                if selected_mode:
                    st.session_state.chat_mode = "A1" if selected_mode == "Quick Compare" else "A2"
                    #st.success(f"{selected_mode} mode selected.")
            #if 'selected_mode' in locals() and selected_mode != "Select a Mode" and not st.session_state.get("files_processed", False):
            if st.session_state.chat_mode and not st.session_state.get("files_processed", False):    
                with st.spinner("Processing resumes..."):
            # Save files to disk
                    target_dir = os.path.join(os.getcwd(), "resumes")
                    os.makedirs(target_dir, exist_ok=True)

                    file_paths = []
                    for file in st.session_state.files:
                        path = os.path.join(target_dir, file["name"])
                        with open(path, "wb") as f:
                            #f.write(file.read())
                            f.write(file["content"])

                        file_paths.append(path)

                    # Run the agent
                    output = agent.run(files=file_paths, query="", chat_mode=st.session_state.chat_mode)

                    # Store results
                    st.session_state["entities"] = json.dumps(output.get("entities", []), indent=2)
                    st.session_state["extracted_texts"] = output.get("extracted_texts", [])
                    st.session_state["final_state"] = output
                    st.session_state["files_processed"] = True

                st.success("Processing complete")
                
             
               
            if st.session_state.get("files_processed", False):
                with right_col:
                    if "active_tab" not in st.session_state:
                        st.session_state.active_tab = "Resumes Entities"

                    st.markdown('<div class="orange-box">Table and Chat Block</div>', unsafe_allow_html=True)
                    with st.container(height=540):
                        st.markdown('</div>', unsafe_allow_html=True)
                        if not st.session_state.get("files") or not st.session_state.get("entities"):
                            st.warning("No resume data found. Please upload resumes on the Home page.")
                        else:
                            tab1, tab2, tab3,tab4 = st.tabs([
                                "Files Details",
                                "Each Resume Entities",
                                "Resumes Entities",
                                "Chat with Resumes",
                                
                            ])

                            # === TAB 1: File Info ===
                            with tab1:
                                st.session_state.active_tab = "Files Details"
                                st.markdown("""
                                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 15px;">
                                    <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRpNdWzAI0uX370i4r81xYDoEse0yivhYFgMQ&s" width="36">
                                    <h3 style="margin: 0; color: white;">Files Details</h3>
                                </div>
                                """, unsafe_allow_html=True)
                                file_data = []
                                for f in st.session_state.files:
                                    file_data.append({
                                        "File Name": f["name"],
                                        "Size (KB)": round(len(f["content"]) / 1024, 2),
                                        "Type": f["type"]
                                    })

                                st.table(file_data)

                            # === TAB 2: Resume Entities ===
                            with tab2:
                                st.session_state.active_tab = "Each Resume Entities"

                                # Add a visual heading with an image
                                st.markdown("""
                                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 15px;">
                                    <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTaaCMqpmlNZ5a2DbxRGioyxEWVSi4QqDgMkw&s" width="36">
                                    <h3 style="margin: 0; color: white;">Each Resume Entities</h3>
                                </div>
                                """, unsafe_allow_html=True)
                                try:
                                    entities = json.loads(st.session_state.entities)
                                    records = []
                                    for record in entities:
                                        data = record["entities"]
                                        records.append({
                                            "Name": data.get("Name", ""),
                                            "Email": data.get("Email", ""),
                                            "Phone": data.get("Phone", ""),
                                            "Experience (Years)": data.get("Experience Years", ""),
                                            "Location": data.get("Location", ""),
                                            "Current Job Title": data.get("Current Job Title", ""),
                                            "Previous Jobs": ", ".join(data.get("Previous Job Titles", []) or []),
                                            "Companies": ", ".join(data.get("Companies Worked At", []) or []),
                                            "Skills": ", ".join(data.get("Skills", []) or []),
                                            "Certifications": ", ".join(
                                                c if isinstance(c, str) else c.get("name", str(c))
                                                for c in data.get("Certifications", []) or []
                                            ),
                                            "Projects": ", ".join(
                                                p if isinstance(p, str) else p.get("name", str(p))
                                                for p in data.get("Projects", []) or []
                                            ),
                                            "Education": ", ".join(
                                                f'{ed.get("degree", "")} - {ed.get("institution", "")}'
                                                for ed in data.get("Education", []) or []
                                            ),
                                            "LinkedIn": data.get("LinkedIn Profile", ""),
                                            "Languages": ", ".join(
                                                l if isinstance(l, str) else l.get("name", str(l))
                                                for l in data.get("Languages", []) or []
                                            )
                                        })

                                    import pandas as pd
                                    df = pd.DataFrame(records)
                                    df.drop_duplicates(subset=["Email", "Phone"], inplace=True)

                                    for i, row in df.iterrows():
                                        file_name = st.session_state.files[i]["name"] if i < len(st.session_state.files) else f"Resume {i + 1}"
                                        st.markdown(f"### {file_name}")
                                        st.dataframe(row.to_frame(name="Value").rename_axis("Field"), use_container_width=True)

                                except Exception as e:
                                    st.error(f"Failed to parse resume data: {e}")
                            with tab3:
                                st.session_state.active_tab = "Resumes Entities"

                                # Add a visual heading with an image
                                st.markdown("""
                                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 15px;">
                                    <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAABNVBMVEX///8AAADm5+i8vsDR09T/tlX/mBE9muLu7/DuhwDr7O14doD/xHfp6uvMzMxlZWbDxcjY2tsuLi+VlpaOj5D/nBGio6RHR0iAgYGcnJ2vr7BxcXIkW4U4OTn/pzO0trdOTk/WeQBfNgBYWFn/vFiWYh67eiV9RwDNdAAkJCT1khDGdg3Ufg7/y3vcnUn/rTVhYGgRERGaXArmiQ+4bgxrQAdXNAaLUwlrTCStezrlli5mQxQlJSUyMzMqGQNBJwSJYi6abjTGjUIZGRlNLgUiFAI0HwNYPx3Ul0eHaD/zu3HeqmdFNSDwq1B5SAg0JhExfbdeXGSsZgxjTC6ad0jIml4WDQF7XzldQh9qUjJCMx8zJxjmsGuqg1BJNBd8WCkIFR8cR2k0hMERK0AWOFIMHy2bZh+Qct5YAAAPLklEQVR4nO2d+2PaRhLHAwhblS1ANuLlcNDAXc4Y+4yxQ3IXv+O82jiOk7hJkzhtmvb//xMO0MxqV1o9kFgJqL6/JEiA9WF3Z2ZnZ6U7dxIlSpQoUaLpKlfZTM2INis5AXyHcWOxOixMGbAYN5FdxakCVuLG4akyRcBa3DB81aZHGDeKk+RpAa7HTeKkqQ3FNfjCipSeCUloFs6nBKjB91VlNW42Q6pcgkvSpkOYM75tLW4wSip0qyk5fiDMy3FzmZLzxjVNye3PIuFGQiiGUFFkQ4qyiISKnK5Vmmub55uH+WJDlYVCxkCopEtNxhnnG2mBjJETKun1x7aAo15ThPnPqAnlDH/y2JJENWPEhIrz5LEmyP5GSqim846AqdS6mFaMlFBpuQAOw//AiCpxPmP/w4zpKAllugXXmrsrK7tvynTKqhSko6pDOKlW3WiV62trh/VmvlgqqJSbjZBQNsdgr7liqmwiFiZtRVVO59Y5PWOtMvRASsSEaoH8/fIKK5xUps4n41PUQmUt5aR8TRvN4aIjVEhbvVmxipyqTNBP5XSp7ohn/GAVSVYjI1RIimrXBriyQoIcya/nV9LFnjufcSW5yAhljGTsLTgStsaGv5E4jPx84Bnf2IqGUM3AH6xzAVdWzuG85gdQznj0T45EExJP4QC48gbOl7wbUVVsWeejy73rrW6/3+9uXQ8exEKYhk5qNaOmwDHmPQkViQ1tjwZbS/pQS2ON/qf3r+2UggmJq+CZGbYRvQhlJqt+MegiGy1d7+w/iZRQAcOwaeMykeFKPKypTOecj647HDyE7F7ShIJzbThyLHZm1G49ZATj33BtRGYIXi858hmQfaqz1qeT13ciREPTZACbTM+F6MTV1Cgb5iXf9+AbM24dkfefK1EQvuEAIiIENlUXQtlswYsuy6ebYg4vmV11cxqt6EW4ywOEw96EVOx+QA/AIVR3f3DvyVAPLve2+gykvm921GgJqSmFcdyT0Az8UgOar2P1DayB1fs3eCIfIeGbc/aidr0J1Rx59zUF2D1IcURbWb3zFA+HX2PztDS7Q71p1s9tl1TfrXu1IZko7ZsX3+UHMEPd7JmWqHOMR0N7RS9CH3IilIkZJS2ody7dvunplolITGrkhC/e+iRUMHRP7RHALa9f65L05Q4eCjsUJyV8t71qRXRqQwxG7xHAPS/AVOq4j+FqFw+F7KeTEd68315dtSLyCRUM1o462CxsD3128uhsZ+f52enXC+ZPEET8PQ7FEHIzwS9WR4Cr278wRwvcuBSXz1Po6PV71Gc+nGWz7XY7mx39k905pb8PEZfQJoUrPHGePTHub6hP716O+UaIP/1sHt/gJyIxmEFHqFM+4uurMZupdvuRGawRxD4eEEOoposQw9x8/PjxxZefVpHPYIQ/nneKSuH8DY7BAQG43bHwjRmzZjtivyb9tCSmDdOyZJz7eXukVYvw53UwpDgKwRNSVvQ0ywEcMe6Q8Yi2SYfXjwURYkjys42OInRIJirg7I90i+1PnfH5xrrFN4F/IRFqGHMqhpCksbAJySB0A8xmn+Hb+tC5YXSG8YluhNBLf+URvnQlxHDmyOrb3AGz2ddsP9Wv4XWImaIPwk+8JvxsnOvxCTXIUqEhxQzMqQdg9hX+FOBj0JyGcBg+CFOf7YDb741Th1xC0kn7rJl55gWYbZ/BWx+wPiZEN3VdXYPJw3t7N0Wnz3eGmJt5orO+fscLcIj4EBuR/XHEEGLk9pYzEOEP8yM2FaKFPbarnXg24VA7KaaDoxGWhBCSKbqtEbffwRmNn0lk2wEd9ysfgNn2V3g3tD8M4eBO37WXYmx5YQXEiKbJb8ICe5Ewm33opwnNRmR/nuAD0X2VG+ewb1nAzxh91PjTCsgmH4MlhTd7eQpsxE90F8eB2BNDqJIJwtuX21QLYqKozu2iZF4CQwmNhS++IeGp8fYn7EAUQ0inO7+sjmPT7e2XL8ixDD8olWEB0EheoNf+4K8Js9nnxvtvdCY2TYshZOZQv3z56fP7Lx/NA04r3DJ4GSProsPE19PbE8HXgzOFtFvgVQwPQlVyXpkuO+XYZEjMdRlreOYXEEM3+DjMgzOi2lDJpRx0mHZac5K5jfDcN+EH6AJLdBdoiCJMK5K9MnGkliMgITQmsjrMD3x5w5EwrIFOfl80oUMr9lx2L4Ql/MoQDoQTkgDcQuj4AQdCH0EpCNswol4ahBCsU58JaZ77tqW3DCHMLoRZGlXBdM3FybPb29sPJ0goO1YJYyUOawwf+SbsMR8HUxw4keEe0yhqYT0P3u11eyz0VuV8KedQti+DE91nBpKvmcVIOAuGjBsEUIEnF24zYFkqUmV2r+EKqa5ar6a5sy4IZyGm2Wc/7ymYBF+wUW3g5WCXujaJWoIfaRyUtD+wByuavR0xlXhgXCMmaXwaUzSlB+zkMiigc1Y/bU/rjxAfWg/2SrbxiPPKCzay9DkQ2yleDwi+3u1AKBd4FfqnbRvgUC1rMxLr22Gs4a++CEmmBiwxOPzg+4L5hLJDIeFr7tFzW6UwWMMtphn8xW1t8BUwudRhKho82cYldNmCwFeD/YEUSPBc6ow5vPXRiKQJr9lhqE6VUKYBf/v96tvyXQvR1bdvd7/TB9iZolI1jmJCGFdl/IxEXIPqMEmMtcCAPEK6i/5xtTwWi4gHfzMP5WhEMhCNsMRcJvM0p20IKDA/gP4+xPZ8OyEVafcAxYLIO/qYybphOhEsPsaWnv2U9FFcuEBPE6KKj9OGZEPF92VKJswVdfTbn3iU6edkIMOFkqUn93xb+zm+b4/9aUJ0UjuhWUt4d3mZh3jFHibDkc67kW46sKywpL66IJqAF0ts9w5zDwkroVnHZAFExCvrYUTcpEciJqMwuNRJdewHhwVSuoviugw6w1Ab162EZKfT71aS5eWrP377/s1+GO0NvdGLrM2gw+iQUrUL3iL3aJkbjYxZgINN2AoBaCUk3etPO4mTvsFHmD39MsZEXWhEsoQ4nGVYCxVGOjOjiQNr9UbwRQs7IUmQ2jqji3CE0iNRacDBJzCk6Hqom9NXbQpy+P+zW/PsA/wExkLlMIBWQgW+9Ls3l72fMlX7ZE8RdjmqbHSoZ49etUHZs5Mb6swxAJodO1QTWghV/OU5w81HI9KbS8yyNlIyZK1qu314cvL12Q178AABMTeQ2ggFaCFEVzHBKBwJR2KG9vpmaSKWfen9pykv7RFAUoATstqbJcT8g81TeOgP42PMnlJzWecJuWpLaZtNZi242adDlQvZCHGjzGSdlHRTywwFuzyxHSOTepxy1oCU0Jo9OpSnsBESXzEh4PKV8bHHllkmCY/umYj6vlNXvSQle/SQDV2uzxLCqwmHoTkQrbkQsnJFOuqoq25xCr2P90w+2uyG3zjDEsLy9GS+YiQ+oaqRlaunNIDe2b9Pm9AHe316swlVaRt2EDoR/nl3Ujm0oULly7cohtF2kqXu1v5I3Q67p0TvmLXu07gbFpcwsGw5SYX6xkvrpi77hpnxEDRbdyq3pRNMSDn+VOpon7cvj+XrU2N0OvfdE03ItGLqmLv3kOqgA+rNU7phm3DCtKLRO/CP9502IOpL/QHzZWL2HzrfDsCP+BtmVY2p+78YdJesLcndJytkD6kSqhHrDtu6VcVy68Kjg+suvTuvv7XHCXXE7JJV0qVqUDWcbzskS/bN6jfHB4O9vcHlvSPbKZGEo3t6BZYT37gZq35uqGDoXCyhKMmazzvB1hvzes89VfHDWC5J2rwSju9NU3W9ecT5RkOT5pkwPbq1Xa7Y5OOt5Uu5IZ9owhB2xqcdUhWFe+fisjTGE00oFddFqWi2I4Sqt4/GOgVCBBRKGDpqcxNZnMJ8+EMjmbizyITjfPACEmKGanEJ07VFJ5QWnVDSCGEMlkYqihNMrTStBul+1lusVXNaBP5QFe7xNckhpBmqpoknFC7NLfrezM0/oSZpbqF3bf4JpUUnlGaA0G1WENC2pMkraQYItWrJLixA4J1zUxUA8ZVGE/6T1l9PoyLke3xjN7O5pOtbBiHuTQBDCYT//Q+t/8VLWA9JCHVyBZbwH5QSwoQwIRRNiClsi6WJh1CqcARVMhrvnJs2wFsM/zcSa0v/+het46gIHeYWYT2+NpbEEHI1r1GbRGsRCaVFJ5QWnVCaNULDRJDM5qTzB6vU4ZQXNRuEWm0sqBOFV64yEFWHsyVzPlJlvcXlfVqRzy3KTB2fq6Au1cc7WY//4w+Ulu5FTdiMmPCHhDAhTAj/ToRSfjwNwNmE8cpVUC1mfWfertwsEKZVeMQU+HHZW9x3KhpH0kwQTknWUI0Ttc03oQvgYhC6AS4CoeYKGD+hGlKKewvGT6g1MuHUoCcWAMW8itsfTrdSAZjg1Wx4fCGE3IxwQpgQJoSREnLXLeIizLU4kwI/anHUBELjZHOm5hYTizeX0EhV8wLMLTziGFrzSTgB4FwSeoTa8084GWD8hJPOJSYFjJ1QK0yohn+xhPv/pvTjg8j8ocgqaNbjc7UYhG7Pc8ssAqHE3fRkqCy+CjoKQs36pCxTOFTnnFDK2R+laKgYQa1+JIRSjlut36tGsTtPzZWbflQOoHrO9Im1vPVsq5iLZEeJz7lFmj+V8BDj991Oxx+1+Q9ggiluwknDtLkjFA8YM6F4PnGEfmYSETRgWELbrTlwx2rLz8WHXNOwqcD/oyEIVeeNcfGolZsyoVO4FJ+4XSc4Ycb9r8WizFQJG+5/LBY1EsKEkEd4vjYDOuwJJMznJk2oCVCuLpKwMG3PHUCFhDAhTAhjV0KYECaE8SshDEXYmiXCEocQ79Ez+V12YVHi8UwQAkWFN8mHMrHJH2uBTzwPWyU7DRXgXlG8NAbmIgI89QE+uTELjYh3Fi7YADWAfzw54B34aC9uupFwOr5ha0TcixTkfuW4OjgL1rSAS8ENCyJZ6A/0dBl8OnNlBhCxm/Yy7Lob3gss2IPISJXADAzFAt4c/ZxuRfNmZwGf/0uKWcqlQsyQhSpeS6oiGQukmtYgZQzNYIB3qMdN1CuleN1GgaqsyVczUq5WpKqJAj9pzeH5ojOnwE/hvnNn0ieMxqP14IDzgVgNAzibCzSMeqEXf5UN778SozZCP+FpKL838Y9BlTCPq2SUKTpX0MWlZnFKxQmJEiVKlCgR6v/IFRlTTCCIeQAAAABJRU5ErkJggg==" width="36">
                                    <h3 style="margin: 0; color: white;">Resumes Entities</h3>
                                </div>
                                """, unsafe_allow_html=True)
                                try:
                                    entities = json.loads(st.session_state.entities)
                                    records = []
                                    for record in entities:
                                        data = record["entities"]
                                        records.append({
                                            "Name": data.get("Name", ""),
                                            "Email": data.get("Email", ""),
                                            "Phone": data.get("Phone", ""),
                                            "Experience (Years)": data.get("Experience Years", ""),
                                            "Location": data.get("Location", ""),
                                            "Current Job Title": data.get("Current Job Title", ""),
                                            "Previous Jobs": ", ".join(data.get("Previous Job Titles", []) or []),
                                            "Companies": ", ".join(data.get("Companies Worked At", []) or []),
                                            "Skills": ", ".join(data.get("Skills", []) or []),
                                            "Certifications": ", ".join(
                                                c if isinstance(c, str) else c.get("name", str(c))
                                                for c in data.get("Certifications", []) or []
                                            ),
                                            "Projects": ", ".join(
                                                p if isinstance(p, str) else p.get("name", str(p))
                                                for p in data.get("Projects", []) or []
                                            ),
                                            "Education": ", ".join(
                                                f'{ed.get("degree", "")} - {ed.get("institution", "")}'
                                                for ed in data.get("Education", []) or []
                                            ),
                                            "LinkedIn": data.get("LinkedIn Profile", ""),
                                            "Languages": ", ".join(
                                                l if isinstance(l, str) else l.get("name", str(l))
                                                for l in data.get("Languages", []) or []
                                            )
                                        })

                                    import pandas as pd
                                    df = pd.DataFrame(records)
                                    df.drop_duplicates(subset=["Email", "Phone"], inplace=True)
                                    st.dataframe(df.T, use_container_width=True)

                                except Exception as e:
                                    st.error(f"Failed to parse resume data: {e}")
                            # === TAB 3: Chatbot Interface ===
                            with tab4:
                                st.session_state.active_tab = "Chat with Resumes"
                                if not st.session_state.files or not st.session_state.get("entities"):
                                    st.warning("Please upload and process resumes first.")
                                    st.stop()

                                st.markdown("""
                                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 15px;">
                                    <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTLuv9GzhLp2OWlFdYb-o1hTEMAWkVG7I27wg&s" width="36">
                                    <h3 style="margin: 0; color: white;">Chat With Resumes</h3>
                                </div>
                                """, unsafe_allow_html=True)

                                user_avatar_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTML0gExaohZHdZW3609F12nUmVc14WXYNx_w&s"
                                bot_avatar_url = "data:image/jpeg;base64,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"

                                if "messages" not in st.session_state:
                                    st.session_state.messages = []

                                chat_display_container = st.container(height=400, border=True)

                                with chat_display_container:
                                    for msg in st.session_state.messages:
                                        if msg["role"] == "user":
                                            st.markdown(
                                                f"""
                                                <div style="display: flex; align-items: flex-start; margin-bottom: 10px;">
                                                    <img src="{user_avatar_url}" width="35" style="border-radius: 50%; margin-right: 10px;">
                                                    <div style="background-color: #e1e1e1; color: black; padding: 10px; border-radius: 10px; max-width: 80%;">
                                                        {msg['content']}
                                                    </div>
                                                </div>
                                                """,
                                                unsafe_allow_html=True
                                            )
                                        else:
                                            st.markdown(
                                                f"""
                                                <div style="display: flex; align-items: flex-start; justify-content: flex-end; margin-bottom: 10px;">
                                                    <div style="background-color: #0084ff; color: white; padding: 10px; border-radius: 10px; max-width: 80%; margin-right: 10px;">
                                                        {msg['content']}
                                                    </div>
                                                    <img src="{bot_avatar_url}" width="35" style="border-radius: 50%;">
                                                </div>
                                                """,
                                                unsafe_allow_html=True
                                            )

                                prompt = st.chat_input("Ask a question about the resumes...")

                                if prompt:
                                    st.session_state.messages.append({"role": "user", "content": prompt})
                                    st.session_state.pending_prompt = prompt
                                    st.session_state.pending_response = True
                                    st.rerun()

                                if st.session_state.get("pending_response"):
                                    pending_prompt = st.session_state.get("pending_prompt")
                                    bot_placeholder = chat_display_container.empty()
                                    with bot_placeholder:
                                        st.markdown(
                                            """
                                            <style>
                                                @keyframes dots {
                                                    0% { content: "."; }
                                                    33% { content: ".."; }
                                                    66% { content: "..."; }
                                                }
                                                .typing {
                                                    display: inline-block;
                                                    font-style: italic;
                                                    overflow: hidden;
                                                }
                                                .typing::after {
                                                    content: "...";
                                                    animation: dots 1s steps(3, end) infinite;
                                                }
                                            </style>
                                            <div style="display: flex; align-items: flex-start; justify-content: flex-end; margin-bottom: 10px;">
                                                <div style="background-color: #0084ff; color: white; padding: 10px; border-radius: 10px; max-width: 80%; margin-right: 10px;">
                                                    <span class="typing">Thinking</span>
                                                </div>
                                                <img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBw8QEBEPEBARDxUXDxEQDxAQDxAQEBIRFREXFxkWFxUYHSkgGBoxHRUWITEiJSorLjouFx81ODMtNyotLisBCgoKDg0OGxAQGC0fHyUtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLf/AABEIAMgAyAMBEQACEQEDEQH/xAAcAAEAAQUBAQAAAAAAAAAAAAAABgEDBAUHAgj/xABFEAACAQICBQYIDAQHAQAAAAAAAQIDEQQFBhIhMUEHE1FhcYEUIjJCUmKR0RYjU1RykpOhwdLh8BczsbIVNGNzg8Lxgv/EABoBAQACAwEAAAAAAAAAAAAAAAAEBQECAwb/xAAtEQEAAgEEAQMCBgMAAwAAAAAAAQIDBBESMSEFE0EVIhQyQlFSoWFxgSMzYv/aAAwDAQACEQMRAD8A7iAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUbHbE+GnqZ9FNpQbV7J6yVyTGmn90W2qj9nn4QL5N/W/Q2/Cz+7X8XH7LdfSSMIuTpuyXpfocc2OuKvO0t6anlO0QwaWmsJNLmWr8ecXuKa3qUR+lOx4+c7bsr4UR+Sf117jlPq8R+lP+m2/kfCmPyT+uvcaT61EfpRMmDjO267h9Iozv8W1/wDX6EnTepVzTtsiZre352X/APGl6D+sifz8Is6uI+Fv/Hl8m/rfoZi7nOviPh6/xxeg/rI7xTfyx+PjbpqM706p4ZxjzLnJrWaU0tVXtt2fuxvTBNk/SzOaN9tmup8psG7eCyX/ACr8pvOlmE6mkm07br/8RYfNpfar8pznDMJP0y38nl8o0Pm0vtV+U5zXZmPS7T+r+mfR01hKKkqL2r0/0I183Dxs2+lT/L+nv4Yx+Rf1/wBDX8RH7H0m38v6e6Gl0HKKlScU2k5aydr8d242rmjprk9KtWszFt0lR2hVTD0ZAAAAAUA1ee4zUhqLfLZ2R4nfBj5SjanJxhGyxiIVvYJ2NmmzjE3fNrct/WzzXqup9y3t16+Vjpse1d5W8PlGJqbYUaj6HqtL2sqq4Lz8JceG6o5Ni9VOVFp8fGh+DOF/T8/xC2x62sY9t/KzXwdWHl05R63F29pCyafLT81ULnvO61Tm4tNcDXDltjtEw0y1i1ZiWzdRNJriesw5Iy1i0dPOZ6zjni8nZGW8TiY0oSqTdlFXf76feScE8vDfFinLeIhzTH4uVapKrLfJ37FwXZ7iyisQ9dgw1w14L2BynFVttGhVqL0o05OP1txi16x3Lr7kVntvqeieYNX8GkurXp+8i3vCfj12Pb7pYeKyPF0ts8PVS4tQcorvRH7d6anFaftsplWIs9R7nu6mR89N/KTW0S25Eb+AxH7seE30TzLnKfNSfjQVl1w4ezd7CbivyjZ571DT+3fevUpAdVcAAAADxVqKKcnsSV2ZiN/ENbW28ofjMQ6k5TfF7F0LgWeOnCqqyW52WTdzZ2AyudXb5EfStv7FxOGbNFfEdpGHBNvM9N1l+TYehthBOXGpLxpvve7uKmuCkTus48NiddoAyKNGJrE9wNVmGR0au1Lm5dMVsfbErtT6diy13jxLet9pRl4epQqOlVVr7YSXku3QQ9H7mmv7WTr4Qdfh5RzheLhStBm1CvjqyweHV1G0q83dQjfdrNfv2E3BEUjnZeen4YpHuT/xK8h0IwmGSlOKxFTjOok4p+rDcu+76zF882Tr5ZlKEji5dvQCwGpzXR7C4lXqU0pcKkLRqJ9q399xPWzvi1OTH5iUUzfIamH8ZfGQ9NLavpIiXxbeV5pdfTL4nxLUnFYeGTluMlQqxqR4Pxl0x4o2pfaXDU4fdxzEuk0K0ZxU4u6aTT6mTond5S9ZrO0rhlhUAAA1OkLnzat5Ot4/4ff+B30+3Lyi6nfj4RwsflXdwzMiwvPycmvEi7X9J9HZ7zhqMnDxHbvpsXPzPSVpJbFsK7/MrOIjqFTHhlUyAACiHYxcfg4VoOM11qW5xa4o45cNckeSetpRKMKkqvMRXjcJvyLW8vsFKzXxKj9r/wA3FKcoyynhqap01x1pzfl1JvfKT4s7zbdef6ZxgAKgAKAeZQTVmrq1muBiY3ZidukB0oyzwaanFPm5vY/Ql6PuImXHxej9O1HvRwt3DUnGFh/tNdDHU5mWt5Ot8Xff63df8SZhmZh5z1KK+79vfykJ2V3SoAABbq01KLi9qaszMTtO7WaxMeUJzSlKE+ZW2Tlqx603sLbHfevNUZKbW4Jhl+FjRpxprgtr6XxftKrJebW3WuLHFa7Mk1dHitVjCLnJqKSu23ZJGsztG8sT4Q3NdOkm44emp/6lS6i+yO9og5dbt+Vwtm49NZLTnFRWtak+Gq4O1/aca6u8y1tqONd2+0d0zpYmSpVFzNR7I7bwk+hPg+pk3FqIvO0sYdTF/EpUSUtr8zxFlqLe/K7OgzENZl7y/CqC12vGatu2qPQJYirOMNwCDaXcotDBzlQox8IqrZPxtWlTfQ5cX1L2kjFp5v22iETp8puYTetahFeiqcrffIxmxxjWOm0tMsN/knKXGUlDF0lC+znaV3FdsHtS7GyPu3zemWrG9Z3dBw9aFSKnCSlFpOMotNNPimZVVqzW20rgasPNsFGvRnSl5y2PofB+01vXeNnfT5ZxZIvDnOU4SdWqsPukpuMupJ2b7iFWu9uL1GozVpj9x0zDUI04RhFWSVkTqxs8ne83tysvGWqoAABar1YwjKcnZJNt9SM1jlLW1uMbofldV4nHKpLpckuhRVor70yyy19rDtCrxT7mbeU0KxagZQHlAzWUqiwsXaMUpVOuT2pdiVn3lbrM0x9qLntPwh5XR/hw2/dh1at31bjNbTWfLnkpyqJneJ87oXmOnT9EdJOfw7jUd6tNJO++a3KXv7OstNPk5wt9Nn5x5bXAUXOTnLak79rJM+EmO22NWyoEM5StKvAsPzVJ2r1U1Cz204bnU7eC6+w74MXOd21YcLbLLeIjaHWIXcLWtK3B7Cvz72TdHl4W8tiQ15G/af8AJZnco1Xg5u8ZqU6V/NnHbJLqau+42qqfUsEcecOomVKAc6zuu8HmUqsN14za6YyjaS+5shXnhk3em0uONTouEugYbERqQjUg7qSUk+pomVnd5u9JpbjZdMtVQAADQaYOpzK1fJ1vjP8Ar3X/AAJejiJv5Q9ZMxTw1Gh3+Yf+1L+6JJ1v5UTReLpsVa3AORaYVtXGYhy9Nf2qxVZ8e+XdW57/AH7I+sbreLbVvsve5HnC0i/nY5o5cHWIXFDrOkTsiXpHJu9EqE5YiKpu0rq+zZzfnX/fQd8Ezz8GGtov4daowUUorci3XfwuAW61RRTk+BmGJfOmn2LxHh9Z4hXk5XhZvV5nzNXqt99yzwxEU8OtJR5Yq/D7zN55V2dK9nPdX3kfj4dYrvLaUcS9VXW23T+9pDtXyvsETw8pPoLJvMMK4/KP2asr/ccvly1v/os7odHmSxgc40//AM2v9mH90iHqfEvUei7+zP8AtvtAHV8Hlr+Rr/FdPrd1/wATtp5nbyrPWOEZvt7+UqO6qAAACziKMakZQkrpppm1bTWd4a3rFo2lCMuqeCZhToT3ycoX9VxvF97SLPL/AOTByhV4o9vNxT0qlsAcy5UspmpxxUFeEko1bebNbIt9TVl3EXPXbzsgarH55IARu0Pry2GHnrL+pGvTZ29z7V5I1iN3DzLqOheReDUucmrVZq8r74R4R7en9C102KKV3ntaafFFK7z2khJSFQNRj67qSUI7UnZdbNoayjHKVoZ4ZhFUoxviKKco2W2rB+VDr6V19p1w5ZrO0t4cEat1foWHiYdYnZlYSGs78FvImaeKx0lPctuzyHvuuYj4dH5IsknKpLGzVoRThRb86ctkmupK67+oxsqfUtRHH24dYMqUA5tncHjMylRhwcad+hJXk+5tkLJ9+XZ6jS2/DaL3JdDweHjShGnBWjFKKJkREQ81kvOS02nuV4y5/CoZAAGPjMVClTnVm7RjFyk+pGa1m0xWGtrRWN5cZzHNqlbEvFN2lrqUPUUXeK7j0NMMVx8FDfLNsnN2DKMfHE0KdaO6UU2vRkt67ndFDlpOO/GV3ivyryhmnN1W69GFSLhOKlFpqUWrpp9KMTG7ExE9oDnPJspNywlVQvt5qrdxXZNbbdqZHvg3RMmliemnwvJ7mCntdFR3N85K39u85Tp5lyjSzKZaP6HUsPJVaj56otsdloRfSlxfWzph01a9pGLTVr2lBKSQwMHMMWo+ImtZq9r7VHdc2a8o32ecsw1lrvf5vZ0iSO2xMNkA0y5MsPjZyr0J+DVm7ztHWpVG+Lit0utexnfHnmraLITR5Kc0hO2th5RfnKrO3btjczkyckzS6n2p3SjIuSuMZKeMqqolt5qjrKL7Zva12JdpHiEjL6nNo2pGzpGHw8KcIwhFQjFKMYxSUUlwSQVVrTad5XAwwc4zCOGoVK0vNjdLpk9y9ppe3Gu8u+mwWzZIpHy5Bl2a1KOIjiU7y13KfrKT8ZPtKyuTjbm9pn0lb4Pa/wAOzYLFQrU4VYO8ZRUovqZaVmLQ8RkxzjvNbdwvmzmqAAAQ/lJVZ4aOp/L5xc8le/q36r/fYm6Hjz89/CFrYnj4cyL2OlN2k2hWkfgtR06j+Km9v+nL0uzdfsIGs03uV5R2m6XUcJ2np1OE1JKSaaaumndNFJMbLiLco8PYZAAAAYGDm2ZU8NSdWo+qMeMpcIpdJre8VaZLxSN3NK+dVpV3idjlttBt6mrwg7eb/wCmKzvKi/E2nNydG0fzqjjaMa1F+rUpvy6VRb4SXBo6zC+rO9d20MNgCgYAAZeKk1FNyaSSu23ZJIMxWbTtDlemmkXhdTm6b+Kg9nry9Ls32K3UZuc7Q9d6VoPYrzv+af6RojLjqPLpvJqqyw0tf+W6j5lPf63df77llponi8h6zwnP9vfyl5JUyoZAAFjFYeFWEqc1rRlFxkulNWNq2ms7w1tWLRtLi+d5bPC150ZbbPxZelB7n++g9FgyxkxxaFBmxzS81YJ27cukh0b0rrYTxJfG0r+Q3tj9F/gQdTpK38x2l6fVTTxLoeT6S4TFJc1VSlxpTtCon9Hj3XRRTMRO0ramatum4DruGWFG7GN9jeIR7OdLsNh04wkq8+EYO8U+uW5f1I+TUUpG0OGTUVr05/mOZ1sVU52rK9tkIrZCKfQuBHxcrzzsrdXqJt4hjkuFZ/lqsRmOJy6usbhZWUrRr02m6c7btZL+vvJuHa8cV56bqOVfbt/x0rRflJwGMShUksJV2J06skoN+rUex99n1GL4bQs+M7popX2rbxRy6axCpgAbNJnelWCwl1Vqpz3KlTtOq30WW7vsjEzx7ScOkyZp2rDn2kmldbF+IviqXoJ7ZfSf4Fdlz8p2eo0PpdMH3W82R8jbrbqWbkuWzxVeFGPF+M/Rgt7/AH0nTFTlbZF1mojBim0u0YTDRpQjTgrRjFRiuhJWLasbPCZLze28r5lqqAAAUAifKBkvP0OfgrzpJt23yp8V3b/aTdFn4X4z1KFrMPOu8OXl530p+gDHxMPOXeed9U0vGedXbHaWZg9IMbSsqeJqpcI67lH2S3FP7tohJpkvvtVNKGa4/mEpYiXONXvq01Z9GxFbb1HJ7m2/h6WuhtOn8/mRnG5liKt1Vq1J7dsZTla69U7zlm877vNZbZItMSxqcLuyFa8pR7Tt90s6dOy2cCxxxNY2Q7zMrR1adKV8NGpCVOaupKz/AH0+4maekx9zemWcd4mHOMdhZUakqct8XbtXBlhE79vVYcsZabsvLM+xuHssPia1JejCrJQv9Hca2x0nt2ivKdoSyjpvmqiovFybttbhRb9riQ744hc4dDiiPuhgY3STHVtlTFVpLjFVJRi+6OxkeUmmmxVnxVZyuhd674bI9pD1OXbwsdPiiPMNoQE7oHXk6jd0/k/yXmKPPzXj1Emr740+C79/sLLT4+Nd3j/V9Z72TjHUJaSVQAVAAAAFGgxMITieTylKcpRryhFybUFTT1U3uvfcWFPULRHSBbQxM9rf8OIfOZfZL8xt9Sn+LH0+P3eZcm8GreEy+yX5jnm1nu04TU/ARH6jB8m9OnOM3iJTs7pOklt4cSmyaXnG26Xgwxiycp8t18F18q/qL3kH6TG/5lxHqX/y1+L0DhOTkq7jfeubT2+0kU0HH9So1GKM1+XSlHQGEbvwhv8A417zvTTRX5RbaGJ+V34ER+Xf2a9519v/AC5fTo/d4+AcfnD+zXvN4rESx9Mj+SvwGj8u/s17yRGXaNmPpcfyanOeSqliXGTxMoSSs2qSd1e/pfu5vGpmPhO0uD2Y233YVDkapRlreGzdt3xEV/2E6mZ+E/Dm9ud9t2X/AAnh87l9ivzHP3U36nP8Xl8ksPnkvsV+Y52ndn6rP8WbT5NYRSisTLYrfyl+Yh303Ke0mvrlq/o/t6/hxH5zL7Je8xOkj9231638P7XMNyeU4zjKVdzSkm4c2lrJPde+4zXSxEueX1y9qzEV2/6m0VZWJe20KOd5nd6AAAAAAAABhQwyGQAAAAFTAoZAAAAqBQAAAAAKgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP/Z" width="35" style="border-radius: 50%;">
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )

                                    try:
                                        target_dir = os.path.join(os.getcwd(), "resumes")
                                        os.makedirs(target_dir, exist_ok=True)
                                        file_paths = []
                                        for file in st.session_state.files:
                                            path = os.path.join(target_dir, file["name"])
                                            if not os.path.exists(path):
                                                with open(path, "wb") as f:
                                                    #f.write(file.read())
                                                    f.write(file["content"])

                                            file_paths.append(path)

                                        result = agent.run(files=file_paths, query=pending_prompt, chat_mode=st.session_state.chat_mode)
                                        if "final_state" in result:
                                            st.session_state["final_state"] = result["final_state"]
                                        answer = result.get("answer", "No response from agent.")

                                    except Exception as e:
                                        answer = f"Error while processing your question: {e}"

                                    bot_placeholder.markdown(
                                        f"""
                                        <div style="display: flex; align-items: flex-start; justify-content: flex-end; margin-bottom: 10px;">
                                            <div style="background-color: #0084ff; color: white; padding: 10px; border-radius: 10px; max-width: 80%; margin-right: 10px;">
                                                {answer}
                                            </div>
                                            <img src="{bot_avatar_url}" width="35" style="border-radius: 50%;">
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )

                                    st.session_state.messages.append({"role": "assistant", "content": answer})
                                    st.session_state.pending_response = False
                                    st.session_state.pending_prompt = None
                                    st.rerun()
                      
