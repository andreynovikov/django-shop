import { useQuery } from '@tanstack/react-query'

import axios from 'axios'

function generateAvatar(fullName, size) {
    // 1. Extract initials (up to 2 characters)
    const names = fullName.trim().split(/\s+/);
    let initials = "";
    
    if (names.length > 0 && names[0] !== "") {
        initials += names[0][0]; // First letter of first name
        if (names.length > 1) {
            initials += names[names.length - 1][0]; // First letter of last name
        }
    }
    initials = initials.toUpperCase();

    // 2. Generate a deterministic background color based on the name string
    let hash = 0;
    for (let i = 0; i < fullName.length; i++) {
        hash = fullName.charCodeAt(i) + ((hash << 5) - hash);
    }
    const color = `hsl(${Math.abs(hash) % 360}, 60%, 50%)`; // HSL guarantees readable vibrancy

    // 3. Create off-screen canvas and draw the avatar
    const canvas = document.createElement("canvas");
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");

    // Draw circular background
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2);
    ctx.fill();

    // Draw initials text
    ctx.fillStyle = "#FFFFFF"; // Clean white text
    ctx.font = `bold ${Math.floor(size * 0.4)}px sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(initials, size / 2, size / 2);

    // 4. Return as data URL
    return canvas.toDataURL("image/png");
}

async function loadAvatar(gravatar, name, size) {
  const d = name.startsWith('+7') ? 'mp' : '404'
  return axios.get(gravatar + '&d=' + d, {
    responseType: 'arraybuffer'
  }).then((response) => {
    // const buffer = URL.createObjectURL(response.data); - with responseType: 'blob'
    const buffer = Buffer.from(response.data, 'binary').toString('base64')
    return `data:${response.headers['content-type'].toLowerCase()};base64,${buffer}`
  }).catch(async () => {
    return generateAvatar(name, size)
  })
}

export default function UserAvatar({ gravatar, name, size = 50, border = false }) {
  const { data: avatar } = useQuery({
    queryKey: ['avatars', { gravatar, name, size }],
    queryFn: () => loadAvatar(gravatar, name, size),
    placeholderData: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
    staleTime: Infinity
  })

  /* eslint-disable @next/next/no-img-element */
  return (
    <img className={"rounded-circle" + (border ? " border border-1" : "")} width={size} height={size} src={avatar} alt={name} />
  )
}
