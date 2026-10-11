
import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import folderIcon from "./icons/folder.png";
import fileIcon from "./icons/files.png";
import fileExplorerIcon from './icons/Windows_10_File_Explorer_icon.png';
import edgeIcon from './icons/edge.png';
import mailIcon from './icons/images.png';
import storeIcon from './icons/store.png';
import cmdIcon from "./icons/images (1).png";
import image3icon from "./icons/THisPC.png";
import './App.css';

const actionDescriptions = {
  open_browser: "Opening browser...",
  visit_website: "Visiting website...",
  download_file: "Downloading file...",
  open_editor: "Opening editor...",
  write_notes: "Writing notes...",
  save_file: "Saving file...",
  check_email: "Checking email...",
  open_attachment: "Opening email attachment...",
};
const fakeFS = {
  id: "root",
  name: "Desktop",
  type: "folder",
  children: [
    {
      id: "f1",
      name: "File1.txt",
      type: "file",
      content: "In a quiet room, a fan hummed unevenly, pushing warm air in slow circles. A notebook lay open on the desk, filled with half-finished ideas, arrows pointing nowhere, and a single sentence underlined twice: This might matter later."
    },{id:"f4",name:"This Pc",type:"folder", children: [
        {
          id: "f5",
          name: "C Drive",
          type: "folder",
          children: [
        {
          id: "f#",
          name: "Vscode.exe",
          type: "file",
          content: "--empty--"
        }
      ]
        }
      ]},
    {
      id: "f2",
      name: "File2.txt",
      type: "file",
      content: "The sky was pale orange when the old clock finally stopped ticking. Nobody noticed at first. Cars still passed, leaves still fell, and somewhere a radio played a song that skipped every third beat."
    },
    {
      id: "d1",
      name: "User",
      type: "folder",
      children: [
        {
          id: "f3",
          name: "backup.exe",
          type: "file",
          content: "--empty--"
        }
      ]
    }
  ]
};



// Simple clock component for taskbar clock
function TaskbarClock() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ color: "white", fontSize: 12, userSelect: "none" }}>
      {time.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
    </div>
  );
}
{/*keyboard*/}
function TaskbarKeyboardBadge({ onClick }) {
  return (
    <div
      onClick={onClick}
      title="On-Screen Keyboard"
      style={{
        width: 32,
        height: 32,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        marginLeft: 6,
        cursor: "pointer",
        userSelect: "none",
        borderRadius: 4,
        transition: "background-color 0.2s",
      }}
      onMouseEnter={(e) =>
        (e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.2)")
      }
      onMouseLeave={(e) =>
        (e.currentTarget.style.backgroundColor = "transparent")
      }
    >
      <img
        src="https://img.icons8.com/ios-filled/50/ffffff/keyboard.png"
        alt="Keyboard"
        width={20}
        height={20}
      />
    </div>
  );
}
// Simple badge component
function Badge({ count }) {
  if (!count) return null;
  return (
    <div
      style={{
        backgroundColor: "red",
        borderRadius: "50%",
        color: "white",
        fontSize: 10,
        fontWeight: "bold",
        width: 16,
        height: 16,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        position: "absolute",
        top: -4,
        right: -4,
      }}
    >
      {count}
    </div>
  );
}

// Taskbar app icon


function AppIcon({ label, icon, badgeCount, url }) {
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      style={{
        marginRight: 12,
        
        position: "relative",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        width: 36,
        textDecoration: "none",
      }}
      title={label}
    >
      <img src={icon} alt={label} style={{ width: 24, height: 24 }} />
      {badgeCount > 0 && (
        <div
          style={{
            position: "absolute",
            top: 0,
            right: 0,
            backgroundColor: "red",
            borderRadius: "50%",
            width: 14,
            height: 14,
            color: "white",
            fontSize: 10,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            fontWeight: "bold",
          }}
        >
          {badgeCount}
        </div>
      )}
    </a>
  );
}
function DesktopIcons({ folder, onOpen }) {
  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 40,
        padding: 20,
        display: "flex",
        flexWrap: "wrap",
        alignContent: "flex-start"
      }}
    >
      {folder.children.map(item => (
        <div
          key={item.id}
          onDoubleClick={() => onOpen(item)}
          style={{
            width: 90,
            margin: 10,
            color: "white",
            textAlign: "center",
            userSelect: "none",
            cursor: "default"
          }}
        >
          <img
            src={item.id === "f4"
      ? image3icon
      : item.type === "folder"
      ? folderIcon
      : fileIcon}
            width={48}
            draggable={false}
          />
          <div style={{ fontSize: 12 }}>{item.name}</div>
        </div>
      ))}
    </div>
  );
}
function FileExplorer({ folder, onBack, onOpen, onClose }) {
  return (
    <div
      style={{
        position: "absolute",
        top: 100,
        left: 150,
        width: 500,
        height: 300,
        background: "#f8f8f8ff",
        color: "rgba(11, 11, 11, 1)",
        
        border: "1px solid #cac4c4ff",
        zIndex: 10
      }}
    >
      <div style={{ padding: 8, background: "#c5c2c2ff" }}>
        {onBack && <button onClick={onBack}>⬅</button>} {folder.name}
        <button onClick={onClose} style={{ float: "right" }}>✕</button>
      </div>

<div style={{ padding: 10 }}>
  {folder.children.map(item => (
    <div
      key={item.id}
      onDoubleClick={() => onOpen(item)}
      style={{
        padding: 6,
        cursor: "default",
        display: "flex",
        alignItems: "center",
        gap: 8
      }}
    >
      <img
        src={item.type === "folder" ? folderIcon : fileIcon} // must be an actual image URL
        width={24}
        height={24}
        draggable={false}
        alt={item.type}
      />
      <span>{item.name}</span>
    </div>
  ))}
</div>
    </div>
  );
}
function FileViewer({ file, onClose }) {
  return (
    <div
      style={{
        position: "absolute",
        top: 140,
        left: 200,
        width: 420,
        height: 260,
        background: "#f2f2f2ff",
        color: "rgba(11, 11, 11, 1)",
        border: "1px solid #afababff",
        zIndex: 20
      }}
    >
      <div style={{ padding: 8, background: "#dfdadaff" }}>
        {file.name}
        <button
          onClick={onClose}
          style={{ float: "right" }}
        >
          ✕
        </button>
      </div>
      <pre style={{ padding: 10, whiteSpace: "pre-wrap" }}>
        {file.content}
      </pre>
    </div>
  );
}
// Windows Homepage with Taskbar

function WindowsHome({ onHomeClick }) {
  const wallpaperURL = "https://wallpaperaccess.com/full/317501.jpg";
  const [currentFolder, setCurrentFolder] = useState(fakeFS);
  const [folderStack, setFolderStack] = useState([]);
  const [openFile, setOpenFile] = useState(null);
  const [explorerOpen, setExplorerOpen] = useState(false);
  function openItem(item) {
    if (item.type === "folder") {
      setFolderStack(prev => [...prev, currentFolder]);
      setCurrentFolder(item);
      setExplorerOpen(true);
    } else {
      setOpenFile(item);
      console.log("FILE OPENED:", item.name); // honeypot log
    }
  }
const apps = [
  {
    label: "File Explorer",
    icon: fileExplorerIcon,
    
    url: "https://www.google.com/search?q=file+explorer", // Placeholder
  },
  {
    label: "Microsoft Edge",
    icon: edgeIcon,
 
    url: "https://www.microsoft.com/edge",
  },
  {
    label: "Outlook",
    icon: mailIcon,
    
    url: "https://outlook.live.com",
  },
  {
    label: "Microsoft Store",
    icon: storeIcon,
    
    url: "https://apps.microsoft.com",
  },
];
  const openAppInPopup = (app) => {
    const features = `width=${app.width},height=${app.height},resizable=yes,scrollbars=yes`;
    window.open(app.url, `${app.label}Window`, features);
  };
  const menuItemStyle = {
  padding: "10px 12px",
  
  borderRadius: 4,
  display: "flex",
  alignItems: "center",
  gap: 10,
  userSelect: "none",
  transition: "background-color 0.2s",
};
  const [isStartOpen, setIsStartOpen] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);
  const divRef = useRef(null);
  const [isTerminalOpen, setIsTerminalOpen] = useState(false);
  const [isKeyboardOpen, setIsKeyboardOpen] = useState(false);
  const enterFullscreen = async () => {
    const element = divRef.current;

    if (element.requestFullscreen) {
      await element.requestFullscreen();
    } else if (element.webkitRequestFullscreen) {
      await element.webkitRequestFullscreen();
    } else if (element.mozRequestFullScreen) {
      await element.mozRequestFullScreen();
    } else if (element.msRequestFullscreen) {
      await element.msRequestFullscreen();
    }

    setIsFullscreen(true);
  };
  return (
   <>
    {!isFullscreen && (
      <div
        onClick={enterFullscreen}
        style={{
          position: "fixed",
          inset: 0,
          background: "black",
          color: "white",
          fontSize: "20px",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          zIndex: 9999,
          
        }}
      >
        Click anywhere to continue
      </div>
    )}

    <div
      ref={divRef}
      style={{
        height: "100vh",
        width: "100vw",
        backgroundImage: `url(${wallpaperURL})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        userSelect: "none",
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-end",
      }}
    >{openFile && (
  <FileViewer
    file={openFile}
    onClose={() => setOpenFile(null)}
  />
)}
        {/* 🔹 DESKTOP FILES (new) */}
  <DesktopIcons folder={fakeFS} onOpen={openItem} />
  {/* 🔹 FILE EXPLORER WINDOW (new) */}
  {explorerOpen && (
    <FileExplorer
      folder={currentFolder}
      onOpen={openItem}
  onBack={() => {
  // If no more folders to go back to, close explorer
  if (folderStack.length === 0) {
    setExplorerOpen(false);
    return;
  }

  const prev = folderStack[folderStack.length - 1];
  setFolderStack(folderStack.slice(0, -1));
  setCurrentFolder(prev);
}}
onClose={() => setExplorerOpen(false)}
/>
  )}
            {/* ✅ Show terminal only if open */}
       {isTerminalOpen && (
  <TerminalWindow onClose={() => setIsTerminalOpen(false)} />
)}
      {/* Taskbar */}
      <div
        style={{
          height: 40,
          width: "100%",
          backgroundColor: "rgba(20, 20, 20, 0.9)",
          display: "flex",
          alignItems: "center",
          padding: "0 12px",
          boxSizing: "border-box",
          borderTop: "1px solid #111",
          fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
          position: "relative",
          
          zIndex: 100,
        }}
      >
        {/* Start button */}
       <div
          onClick={() => setIsStartOpen((open) => !open)}
          style={{position: "relative",left:"650px",
            width: 40,
            height: 40,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            
            borderRadius: 6,
            marginRight: 12,
            transition: "background-color 0.2s",
            userSelect: "none",
          }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.backgroundColor = "rgba(0, 120, 215, 0.5)")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.backgroundColor = "transparent")
          }
          title="Start"
        >
          {/* Windows logo SVG */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="25"
            height="25"
            viewBox="0 0 48 48"
            fill="rgba(100, 183, 252, 1)"
          >
            <path d="M6 6h16v16H6zM26 6h16v16H26zM6 26h16v16H6zM26 26h16v16H26z" />
          </svg>
        </div>

        {/* App icons */}
        <div
          style={{position: "relative",left:"650px",
            display: "flex",
            flexGrow: 1,
            justifyContent: "flex-start",
            alignItems: "center",
          }}
        >
        {apps.map(({ label, icon, badgeCount, url }, idx) => (
  <AppIcon
    key={idx}
    label={label}
    icon={icon}
    badgeCount={badgeCount}
    url={url}
  />
))}
        </div>

        {/* System tray */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 14,
            color: "white",
            fontSize: 14,
            userSelect: "none",
          }}
        >
          {/* Network icon */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            height="16"
            width="16"
            fill="white"
            viewBox="0 0 24 24"
          >
            <path d="M12 4c4.41 0 8 3.59 8 8h-2a6 6 0 0 0-12 0H4c0-4.41 3.59-8 8-8z" />
            <circle cx="12" cy="14" r="2" />
          </svg>

          {/* Volume icon */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            height="16"
            width="16"
            fill="white"
            viewBox="0 0 24 24"
          >
            <path d="M5 9v6h4l5 5V4L9 9H5z" />
          </svg>
          
          
          <TaskbarKeyboardBadge onClick={() => setIsKeyboardOpen(!isKeyboardOpen)} />
          {/* Clock */}
          <TaskbarClock />
        </div>

        {/* Start Menu */}
        {isStartOpen && (
          <div
            style={{
              position: "absolute",
              bottom: 40,
              left: 450,
              height:750,
              width: 750,
              backgroundColor: "#2f2f2f",
              borderRadius: 6,
              boxShadow: "0 0 10px rgba(0,0,0,0.8)",
              padding: 10,
              color: "white",
              fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
              zIndex: 9999,
            }}
          >
            <div
              onClick={() => {
    setIsTerminalOpen(true); // Open terminal here
    setIsStartOpen(false);   // Close start menu
  }}
              style={{
                padding: "10px 12px",
                
                borderRadius: 4,
                display: "flex",
                alignItems: "center",
                gap: 10,
                userSelect: "none",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#0078d7")}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
            >
              <img src={cmdIcon} alt="Command Prompt" width={20} height={20} />
              <span>Command Prompt</span>
            </div>

        
 {/* Youtube*/}
   <a
  href="https://www.youtube.com"
  onClick={(e) => {
     e.preventDefault();
     window.open(
       "https://www.youtube.com",
       "popupWindow",
       "width=600,height=400,scrollbars=yes,resizable=yes"
     );
   }}
  rel="noopener noreferrer"
  style={{ ...menuItemStyle, textDecoration: "none", color: "white" }}
  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#0078d7")}
  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
>
  <img src="https://img.icons8.com/ios-filled/24/ffffff/youtube-play.png" alt="YouTube" />
  <span>YouTube</span>
</a>
    {/* Xbox */}
    <a
  href="https://www.xbox.com"
  onClick={(e) => {
     e.preventDefault();
     window.open(
       "https://www.xbox.com",
       "popupWindow",
       "width=600,height=400,scrollbars=yes,resizable=yes"
     );
   }}
  rel="noopener noreferrer"
  style={{ ...menuItemStyle, textDecoration: "none", color: "white" }}
  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#107C10")}
  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
>
  <img src="https://img.icons8.com/ios-filled/24/ffffff/xbox.png" alt="Xbox" />
  <span>Xbox</span>
</a>
    {/* Paint */}
    <a
      href="https://jspaint.app"
        onClick={(e) => {
     e.preventDefault();
     window.open(
       "https://jspaint.app",
       "popupWindow",
       "width=600,height=400,scrollbars=yes,resizable=yes"
     );
   }}
      rel="noopener noreferrer"
      style={{ ...menuItemStyle, textDecoration: "none", color: "white" }}
      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#0078d7")}
      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
    >
      <img src="https://img.icons8.com/ios-filled/24/ffffff/paint.png" alt="Paint" />
      <span>Paint</span>
    </a>

   
   
            <div
              style={{
                padding: "10px 12px",
                cursor: "default",
                color: "#999",
                marginTop: 10,
                fontSize: 12,
                userSelect: "none",
              }}
            >
            User 
            </div>
          </div>
        )}
      </div>
    </div>
      </>
  );
}

/*function TerminalWindow({ onClose }) {
  const [shellHistory, setShellHistory] = useState([]);
  const [shellInput, setShellInput] = useState("");
  const shellRef = useRef(null);

  const [pos, setPos] = useState({ x: 100, y: 100 });
  const [dragging, setDragging] = useState(false);
  const [rel, setRel] = useState(null);

  // 🔥 Attack Commands (Attacker Script)
  const attackCommands = [
    "admin",
    "root",
    "123456",
    "ls",
    "cd /root",
    "whoami",
    "ping google.com",
    "chmod +x file.sh",
    "./file.sh",
    "del file.txt"
  ];

  // 🔹 Identify attack type
  const getAttackType = (cmd) => {
    if (["admin", "root", "123456"].includes(cmd)) return "brute_force";
    if (cmd.includes("ping")) return "recon";
    return "post_exploitation";
  };

  // 🔹 Execute command (used by script)
  const handleShellSubmit = async (inputCmd = null) => {
    const cmd = inputCmd ? inputCmd : shellInput.trim();
    if (!cmd) return;

    try {
      const res = await axios.post("http://localhost:5000/trap", {
        command: cmd,
        attack_type: getAttackType(cmd),
      });

      const response = res.data.response;

      setShellHistory((prev) => [...prev, { cmd, response }]);
    } catch {
      setShellHistory((prev) => [
        ...prev,
        { cmd, response: "Error: backend unreachable" },
      ]);
    }

    setShellInput("");
  };
  // 🔥 AUTOMATED ATTACK SCRIPT
  useEffect(() => {
    let count = 0;

    const runAttack = async () => {
      if (count >= 100) return;

      const cmd =
        attackCommands[Math.floor(Math.random() * attackCommands.length)];

      // show typing effect
      setShellInput(cmd);

      setTimeout(async () => {
        await handleShellSubmit(cmd);
      }, 200);

      count++;

      setTimeout(runAttack, Math.random() * 800 + 300);
    };

    runAttack();
  }, []);

  // 🔹 Dragging logic (unchanged)
  const onMouseDown = (e) => {
    if (e.button !== 0) return;

    const rect = e.currentTarget.getBoundingClientRect();

    setDragging(true);
    setRel({
      x: e.pageX - rect.left,
      y: e.pageY - rect.top,
    });

    e.stopPropagation();
    e.preventDefault();
  };

  const onMouseUp = () => setDragging(false);

  const onMouseMove = (e) => {
    if (!dragging) return;

    setPos({
      x: e.pageX - rel.x,
      y: e.pageY - rel.y,
    });

    e.stopPropagation();
    e.preventDefault();
  };

  return (
    <div
      style={{
        position: "absolute",
        top: pos.y,
        left: pos.x,
        width: "80%",
        height: "80%",
        background: "#111",
        borderRadius: 6,
        display: "flex",
        flexDirection: "column",
      }}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
    >
    
      <div
        onMouseDown={onMouseDown}
        style={{
          background: "#222",
          padding: "10px",
          cursor: "move",
          color: "#fff",
        }}
      >
        Fake SSH Terminal (Automated Attack Running...)
      </div>

      
      <div
        ref={shellRef}
        style={{
          flexGrow: 1,
          background: "#000",
          color: "#0f0",
          padding: 15,
          overflowY: "auto",
          fontFamily: "monospace",
        }}
      >
        {shellHistory.map((item, i) => (
          <div key={i}>
            <div>
              <span style={{ color: "#0ff" }}>C:\Users\Dell&gt;</span>{" "}
              {item.cmd}
            </div>
            <div>{item.response}</div>
          </div>
        ))}

       
        <div>
          <span style={{ color: "#0ff" }}>C:\Users\Dell&gt;</span>{" "}
          {shellInput}
          <span className="blinking-cursor">█</span>
        </div>
      </div>
    </div>
  );
}

export default TerminalWindow;
*/






























function TerminalWindow({ onClose }) {
  const [shellHistory, setShellHistory] = useState([]);
  const [shellInput, setShellInput] = useState("");
  const shellRef = useRef(null);
    const [pos, setPos] = useState({ x: 100, y: 100 }); // initial position
const [dragging, setDragging] = useState(false);
const [rel, setRel] = useState(null); 
  const handleShellSubmit = async () => {
    const cmd = shellInput.trim();
    if (!cmd) return;

    try {
      const res = await axios.post("http://localhost:5000/trap", { command: cmd });
      const response = res.data.response;
      setShellHistory((prev) => [...prev, { cmd, response }]);
    } catch {
      setShellHistory((prev) => [...prev, { cmd, response: "Error: backend unreachable" }]);
    }
    setShellInput("");
  };
const onMouseDown = (e) => {
  if (e.button !== 0) return; // only left click

  const rect = e.currentTarget.getBoundingClientRect();

  setDragging(true);
  setRel({
    x: e.pageX - rect.left,
    y: e.pageY - rect.top,
  });

  e.stopPropagation();
  e.preventDefault();
};

const onMouseUp = (e) => {
  setDragging(false);
};

const onMouseMove = (e) => {
  if (!dragging) return;

  setPos({
    x: e.pageX - rel.x,
    y: e.pageY - rel.y,
  });

  e.stopPropagation();
  e.preventDefault();
};
  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleShellSubmit();
    } else if (e.key === "Backspace") {
      e.preventDefault();
      setShellInput((prev) => prev.slice(0, -1));
    } else if (e.key.length === 1) {
      setShellInput((prev) => prev + e.key);
    }
  };
useEffect(() => {
  document.addEventListener("mousemove", onMouseMove);
  document.addEventListener("mouseup", onMouseUp);
  return () => {
    document.removeEventListener("mousemove", onMouseMove);
    document.removeEventListener("mouseup", onMouseUp);
  };
}, [dragging, rel]);
  useEffect(() => {
    if (shellRef.current) {
      shellRef.current.focus();
    }
  }, []);

  return (
    <div
      style={{
     position: "absolute",
    top: pos.y,
    left: pos.x,
    width: 600,
    height: 400,
    backgroundColor: "#000",
    color: "rgba(237, 241, 237, 1)",
    border: "1px solid #555",
    borderRadius: 4,
    boxShadow: "0 0 20px rgba(0,0,0,0.6)",
    display: "flex",
    flexDirection: "column",
    fontFamily: "monospace",
    zIndex: 1000,
    userSelect: dragging ? "none" : "auto",
      }}
    >
      {/* Title bar */}
      <div
        style={{
      height: 30,
      backgroundColor: "#1e1e1e",
      color: "#fff",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0 10px",
      fontSize: 14,
      
    }}
    onMouseDown={onMouseDown}
  >
        <span>Command Prompt</span>
        <button
          onClick={onClose}
          style={{
            background: "none",
            color: "white",
            border: "none",
            fontSize: 16,
           
          }}
        >
          ➖  ⬜  ✕
        </button>
      </div>

      {/* Terminal content */}
      <div
        ref={shellRef}
        tabIndex={0}
        onKeyDown={handleKeyDown}
        style={{
          flexGrow: 1,
          overflowY: "auto",
          padding: 10,
          outline: "none",
          whiteSpace: "pre-wrap",
        }}
      >
        {shellHistory.map(({ cmd, response }, i) => (
          <div key={i}>
            <div>
              <span>C:\Users\Dell&gt;</span> {cmd}
            </div>
            <div>{response}</div>
          </div>
        ))}

        <div>
          <span>C:\Users\Dell&gt;</span> {shellInput}
          <span className="blinking-cursor">█</span>
        </div>
      </div>
    </div>
  );
}
function App() {
  const [actions, setActions] = useState([]);
  const [currentAction, setCurrentAction] = useState(null);
  const [shellHistory, setShellHistory] = useState([]);
  const [shellInput, setShellInput] = useState("");
  const shellRef = useRef(null);
  const [showTerminal, setShowTerminal] = useState(false);
  const [isStartMenuOpen, setIsStartMenuOpen] = useState(false);
 const [isTerminalOpen, setIsTerminalOpen] = useState(false);
  useEffect(() => {
    if (!showTerminal) return;

    const eventSource = new EventSource("http://localhost:5000/stream");

    eventSource.addEventListener("simulation", (e) => {
      const data = JSON.parse(e.data);
      setCurrentAction(data.action);
      setActions((prev) => [...prev, data.action]);
    });

    return () => {
      eventSource.close();
    };
  }, [showTerminal]);
   useEffect(() => {
    if (shellRef.current) {
      shellRef.current.focus();
    }
  }, [isTerminalOpen]);

  useEffect(() => {
    if (shellRef.current) {
      shellRef.current.focus();
      shellRef.current.scrollTop = shellRef.current.scrollHeight;
    }
  }, [shellHistory, shellInput]);

  const handleSimulate = () => {
    fetch("http://localhost:5000/simulate", { method: "POST" });
  };

  const toggleStartMenu = () => {
    setIsStartMenuOpen((prev) => !prev);
  };
const openCmd = () => {
    setIsTerminalOpen(true);
    setIsStartMenuOpen(false);
  };
  const handleShellSubmit = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    const cmd = shellInput.trim();
    if (!cmd) return;

    try {
      const res = await axios.post("http://localhost:5000/trap", { command: cmd });
      const response = res.data.response;

      setShellHistory((prev) => [...prev, { cmd, response }]);
    } catch (error) {
      setShellHistory((prev) => [...prev, { cmd, response: "Error: backend unreachable" }]);
    }
    setShellInput("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleShellSubmit();
    } else if (e.key === "Backspace") {
      e.preventDefault();
      setShellInput((prev) => prev.slice(0, -1));
    } else if (e.key.length === 1) {
      setShellInput((prev) => prev + e.key);
    }
  };

  const renderTerminal = () => (
    <div style={{ padding: 20, fontFamily: "monospace" }}>
      <h1>Fake User Behavior Simulation</h1>
      <button onClick={handleSimulate}>Start Simulation</button>

      <div style={{ marginTop: 40 }}>
        <h1>Fake SSH Shell Trap</h1>
        <div
          id="shell-output"
          ref={shellRef}
          tabIndex={0}
          onKeyDown={handleKeyDown}
          style={{
            background: "#000",
            color: "rgba(246, 250, 246, 1)",
            padding: 20,
            height: 300,
            overflowY: "auto",
            borderRadius: 4,
            fontFamily: "monospace",
            whiteSpace: "pre-wrap",
            border: "1px solid rgba(12, 12, 12, 1)",
            outline: "none",
            cursor: "text",
          }}
        >
          {shellHistory.length === 0 && <p style={{ color: "#666" }}>Microsoft Windows</p>}

          {shellHistory.map(({ cmd, response }, i) => (
            <div key={i}>
              <div>
                <span style={{ color: "rgba(249, 252, 252, 1)" }}>C:\Users\Dell&gt;</span>
                {cmd}
              </div>
              <div>{response}</div>
            </div>
          ))}

          <div>
            <span style={{ color: "rgba(238, 241, 241, 1)" }}>C:\Users\Dell&gt;</span> {shellInput}
            <span className="blinking-cursor">█</span>
          </div>
        </div>
      </div>
    </div>
  );

  return showTerminal ? (
  <div
    style={{
      height: "100vh",
      width: "100vw",
      boxSizing: "border-box",
      padding: 20,
      fontFamily: "monospace",
      display: "flex",
      flexDirection: "column",
    }}
  >
    <h1 style={{ margin: "0 0 12px 0" }}>Fake User Behavior Simulation</h1>
    <button onClick={handleSimulate} style={{ marginBottom: 20 }}>
      Start Simulation
    </button>

    <h1 style={{ margin: "0 0 12px 0" }}>Fake SSH Shell Trap</h1>
    <div
      id="shell-output"
      ref={shellRef}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      style={{
        background: "#000",
        color: "rgba(246, 250, 246, 1)",
        padding: 20,
        flexGrow: 1,
        overflowY: "auto",
        borderRadius: 4,
        fontFamily: "monospace",
        whiteSpace: "pre-wrap",
        border: "1px solid rgba(12, 12, 12, 1)",
        outline: "none",
        cursor: "text",
        minHeight: 0, // important for flexbox overflow
      }}
    >
      {shellHistory.length === 0 && <p style={{ color: "#666" }}>Microsoft Windows</p>}

      {shellHistory.map(({ cmd, response }, i) => (
        <div key={i}>
          <div>
            <span style={{ color: "rgba(249, 252, 252, 1)" }}>C:\Users\Dell&gt;</span>
            {cmd}
          </div>
          <div>{response}</div>
        </div>
      ))}

      <div>
        <span style={{ color: "rgba(238, 241, 241, 1)" }}>C:\Users\Dell&gt;</span> {shellInput}
        <span className="blinking-cursor">█</span>
      </div>
    </div>
  </div>
) : (
 <>
      <WindowsHome onHomeClick={() => setIsTerminalOpen(true)} />

      {isTerminalOpen && (
        <TerminalWindow onClose={() => setIsTerminalOpen(false)} />
      )}
    </>
);
}

export default App;
