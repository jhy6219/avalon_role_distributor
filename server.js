const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

// 정적 파일 제공
app.use(express.static('public'));
app.use(express.json());

// 게임 데이터 저장소
const gameRooms = new Map();

// 역할 배정 함수
function assignRoles(playerCount, includeOberon, includeMordred) {
    const roleConfig = {
        5: { merlin: 1, percival: 1, servant: 2, assassin: 1, minion: 0 },
        6: { merlin: 1, percival: 1, servant: 2, assassin: 1, minion: 1 },
        7: { merlin: 1, percival: 1, servant: 2, assassin: 1, minion: 2 },
        8: { merlin: 1, percival: 1, servant: 3, assassin: 1, minion: 2 },
        9: { merlin: 1, percival: 1, servant: 4, assassin: 1, minion: 2 },
        10: { merlin: 1, percival: 1, servant: 4, assassin: 1, minion: 3 }
    };

    const config = { ...roleConfig[playerCount] };

    // 특수 캐릭터 추가
    if (includeMordred && config.minion > 0) {
        config.minion -= 1;
        config.mordred = 1;
    }

    if (includeOberon && config.minion > 0) {
        config.minion -= 1;
        config.oberon = 1;
    }

    // 역할 리스트 생성
    const roles = [];
    for (const [role, count] of Object.entries(config)) {
        for (let i = 0; i < count; i++) {
            roles.push(role);
        }
    }

    // 역할 섞기
    for (let i = roles.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [roles[i], roles[j]] = [roles[j], roles[i]];
    }

    return roles;
}

// 방 코드 생성
function generateRoomCode() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < 6; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

// 라우트
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/room/:roomCode', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'room.html'));
});

// API 엔드포인트
app.post('/api/create-room', (req, res) => {
    const { hostName, includeOberon, includeMordred } = req.body;
    
    if (!hostName) {
        return res.status(400).json({ error: '호스트 이름을 입력해주세요.' });
    }

    let roomCode;
    do {
        roomCode = generateRoomCode();
    } while (gameRooms.has(roomCode));

    const room = {
        roomCode,
        hostName,
        includeOberon: includeOberon || false,
        includeMordred: includeMordred || false,
        players: [{
            id: uuidv4(),
            name: hostName,
            isHost: true,
            role: '',
            socketId: null
        }],
        gameState: {
            phase: 'lobby',
            round: 1,
            currentLeader: 0,
            teamProposal: [],
            votes: {},
            missionVotes: {},
            missionResults: [],
            evilWins: 0,
            goodWins: 0
        },
        createdAt: new Date()
    };

    gameRooms.set(roomCode, room);
    res.json({ success: true, roomCode });
});

app.post('/api/join-room', (req, res) => {
    const { roomCode, playerName } = req.body;
    
    if (!roomCode || !playerName) {
        return res.status(400).json({ error: '방 코드와 플레이어 이름을 모두 입력해주세요.' });
    }

    const room = gameRooms.get(roomCode.toUpperCase());
    if (!room) {
        return res.status(404).json({ error: '존재하지 않는 방입니다.' });
    }

    if (room.players.find(p => p.name === playerName)) {
        return res.status(400).json({ error: '이미 존재하는 플레이어 이름입니다.' });
    }

    if (room.players.length >= 10) {
        return res.status(400).json({ error: '방이 가득 찼습니다.' });
    }

    const player = {
        id: uuidv4(),
        name: playerName,
        isHost: false,
        role: '',
        socketId: null
    };

    room.players.push(player);
    res.json({ success: true, roomCode: room.roomCode });
});

app.get('/api/room/:roomCode', (req, res) => {
    const room = gameRooms.get(req.params.roomCode.toUpperCase());
    if (!room) {
        return res.status(404).json({ error: '존재하지 않는 방입니다.' });
    }

    res.json({
        roomCode: room.roomCode,
        hostName: room.hostName,
        includeOberon: room.includeOberon,
        includeMordred: room.includeMordred,
        players: room.players.map(p => ({
            name: p.name,
            isHost: p.isHost,
            role: p.role
        })),
        gameState: room.gameState
    });
});

// Socket.IO 연결 처리
io.on('connection', (socket) => {
    console.log('사용자 연결:', socket.id);

    socket.on('join-room', (data) => {
        const { roomCode, playerName } = data;
        const room = gameRooms.get(roomCode);
        
        if (room) {
            const player = room.players.find(p => p.name === playerName);
            if (player) {
                player.socketId = socket.id;
                socket.join(roomCode);
                
                // 방의 모든 사용자에게 플레이어 목록 업데이트 전송
                io.to(roomCode).emit('players-updated', {
                    players: room.players.map(p => ({
                        name: p.name,
                        isHost: p.isHost,
                        role: p.role,
                        connected: !!p.socketId
                    }))
                });
            }
        }
    });

    socket.on('start-game', (data) => {
        const { roomCode, playerName } = data;
        const room = gameRooms.get(roomCode);
        
        if (room && room.players.find(p => p.name === playerName && p.isHost)) {
            if (room.players.length < 5) {
                socket.emit('error', { message: '최소 5명의 플레이어가 필요합니다.' });
                return;
            }

            // 역할 배정
            const roles = assignRoles(room.players.length, room.includeOberon, room.includeMordred);
            room.players.forEach((player, index) => {
                player.role = roles[index];
            });

            // 게임 상태 초기화
            room.gameState = {
                phase: 'role_reveal',
                round: 1,
                currentLeader: 0,
                teamProposal: [],
                votes: {},
                missionVotes: {},
                missionResults: [],
                evilWins: 0,
                goodWins: 0
            };

            // 모든 플레이어에게 게임 시작 알림
            io.to(roomCode).emit('game-started', {
                gameState: room.gameState,
                players: room.players.map(p => ({
                    name: p.name,
                    isHost: p.isHost,
                    role: p.role
                }))
            });
        }
    });

    socket.on('restart-game', (data) => {
        const { roomCode, playerName } = data;
        const room = gameRooms.get(roomCode);
        
        if (room && room.players.find(p => p.name === playerName && p.isHost)) {
            // 게임 상태 초기화 (역할만 제거, 플레이어는 유지)
            room.players.forEach(player => {
                player.role = '';
            });
            
            room.gameState = {
                phase: 'lobby',
                round: 1,
                currentLeader: 0,
                teamProposal: [],
                votes: {},
                missionVotes: {},
                missionResults: [],
                evilWins: 0,
                goodWins: 0
            };

            // 모든 플레이어에게 로비 복귀 알림
            io.to(roomCode).emit('game-restarted', {
                gameState: room.gameState,
                players: room.players.map(p => ({
                    name: p.name,
                    isHost: p.isHost,
                    role: p.role
                }))
            });
        }
    });

    socket.on('disconnect', () => {
        console.log('사용자 연결 해제:', socket.id);
        
        // 연결이 끊어진 플레이어의 socketId 제거
        for (const room of gameRooms.values()) {
            const player = room.players.find(p => p.socketId === socket.id);
            if (player) {
                player.socketId = null;
                
                // 방의 다른 사용자들에게 플레이어 목록 업데이트 전송
                io.to(room.roomCode).emit('players-updated', {
                    players: room.players.map(p => ({
                        name: p.name,
                        isHost: p.isHost,
                        role: p.role,
                        connected: !!p.socketId
                    }))
                });
                break;
            }
        }
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`서버가 포트 ${PORT}에서 실행 중입니다.`);
});