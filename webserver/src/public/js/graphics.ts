import { Receiver } from '../../common/simulation';
import { Position } from '../../common/simulation';
/**No typesrpit types for those libs */
let WHS = require("whs");
let THREE = require("three");



export interface Size {
    length: number;
    heigth: number;
    width: number;
}
export interface TableSettings {
    virtualSize: Size;
    realSize: Size;

}
export interface ScaleSettings {
    x: number;
    y: number;
    z: number;
}
export interface MicrophoneSettings {
    scale: ScaleSettings,
    meshColor: number;
    referenceMeshColor: number;
}
export class Settings {
    table: TableSettings;
    scale: ScaleSettings;
    microphone: MicrophoneSettings;

    constructor() {
        this.table = {
            virtualSize: {
                length: 27.4 * 2,   // z- axis
                heigth: 16.2,    //y axis
                width: 15.25 * 2   //x axis
            },

            realSize: {
                length: 274,// cm
                heigth: 76,
                width: 152.5
            }
        };

        this.microphone = {
            scale: {
                x: 8,
                y: 8,
                z: 8
            },
            meshColor: 0x696969,
            referenceMeshColor: 0x119911
        }

        this.calcScale();
    }

    calcScale() {
        this.scale = {
            x: this.table.realSize.width / this.table.virtualSize.width,
            y: this.table.realSize.heigth / this.table.virtualSize.heigth,
            z: this.table.realSize.length / this.table.virtualSize.length
        }
    }
}
export function init(microphones: Array<Receiver>) {
    table.addTo(app);
    createMicrophoneMeshes(microphones);
    createConstObjects();
    hookUpDebugGlobals();

    app.start();
}
export function spawnFadedSphere(x: number, y: number, z: number, timeout: number = 5) {
    const loopIncrement = 1 / 60 / timeout;
    const sphere = new WHS.Sphere({
        geometry: {
            radius: 1,
            widthSegments: 16,
            heigthSegments: 12
        },

        material: new THREE.MeshBasicMaterial({
            color: 0xff0000,
            transparent: true,
            opacity: 1.0
        }),

        position: {
            x: x,
            y: y,
            z: z
        }
    });

    const animationLoop = new WHS.Loop((clock: any) => {
        sphere.material.opacity -= loopIncrement;
        if (clock.getElapsedTime() > timeout) {
            animationLoop.stop(app);
            app.remove(sphere);
        }
    });

    sphere.addTo(app);
    animationLoop.start(app);

}
export function spawnFadedRing(x: number, y: number, z: number, timeout: number = 5) {
    const loopIncrement = 1 / 60 / timeout;
    const ring = new WHS.Ring({
        geometry: {
            innerRadius: 2,
            outerRadius: 1,
            thetaSegments: 16,
            phiSegments: 16
        },

        material: new THREE.MeshBasicMaterial({
            color: 0xff0000,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 1.0
        }),
        position: {
            x: x,
            y: y,
            z: z
        },
        rotation: {
            x: -Math.PI / 2
        }
    });

    const animationLoop = new WHS.Loop((clock: any) => {
        ring.scale.x += loopIncrement
        ring.scale.y += loopIncrement;
        ring.scale.z += loopIncrement;
        if (ring.material.opacity > 0) {
            ring.material.opacity -= loopIncrement;
        }
        if (clock.getElapsedTime() > timeout) {
            animationLoop.stop(app);
            app.remove(ring);
        }
    });

    ring.addTo(app);
    animationLoop.start(app);

}
export function markPoint(x: number, y: number, z: number, timoutPt = 30, timoutSig = 5) {
    spawnFadedSphere(x, y, z, timoutPt);
    spawnFadedRing(x, y, z, timoutSig);
}
export function updateMicrohoneMeshes(microphones: Array<Receiver>) {
    for (let [idx, mic] of microphones.entries()) {
        let mesh = micObjects[idx];
        mesh.position = mapRealToVirtualCoord(mic.pos);
        if (mic.isReference) {
            mesh.material.color.setHex(settings.microphone.referenceMeshColor);
        }
        else {
            mesh.material.color.setHex(settings.microphone.meshColor);
        }
    }

}
//Real position in meters, virtual: cm
export function mapRealToVirtualCoord(realPos: Position): Position {
    return {
        x: realPos.x * 100 / settings.scale.x,
        y: realPos.y * 100 / settings.scale.y,
        z: realPos.z * 100 / settings.scale.z
    }
}

function createConstObjects() {
    new WHS.Plane({
        geometry: {
            width: 100,
            height: 100
        },

        material: new THREE.MeshBasicMaterial({
            color: 0x447F8B
        }),

        rotation: {
            x: - Math.PI / 2
        }
    }).addTo(app);

    new WHS.PointLight({
        light: {
            intensity: 0.5,
            distance: 100
        },

        shadow: {
            fov: 90
        },

        position: new THREE.Vector3(0, 30, 10)
    }).addTo(app);

    new WHS.AmbientLight({
        light: {
            intensity: 0.4
        }
    }).addTo(app);

}
function hookUpDebugGlobals() {
    (<any>window).mic = mic;
    (<any>window).table = table;
    (<any>window).spawnFadedRing = spawnFadedRing;
    (<any>window).spawnFadedSphere = spawnFadedSphere;
    (<any>window).markPoint = markPoint;
    (<any>window).app = app;
}
function createMicrophoneMeshes(microphones: Array<Receiver>) {
    let materialColor: number;

    for (let mic of microphones) {
        if (mic.isReference)
            materialColor = settings.microphone.referenceMeshColor;
        else
            materialColor = settings.microphone.meshColor;

        let mesh: any = new WHS.Importer({
            loader: new THREE.ObjectLoader(),
            parser(object: any, material: any) { // data from loader
                console.log(object);
                return object // should return your .native (mesh in this case)
            },
            url: `/models/mic.json`,
            position: {
                x: mic.pos.x * 100 / settings.scale.x,
                y: mic.pos.y * 100 / settings.scale.y,
                z: mic.pos.z * 100 / settings.scale.z
            },
            scale: [8, 8, 8],
            rotation: {
                x: -Math.PI / 2,
                y: 0,
                z: 0
            },
            shadow: true,
            material: new THREE.MeshPhongMaterial({
                color: materialColor
            }),
            modules: [
                new WHS.TextureModule({
                    url: `/images/micTexture.png`
                })
            ]

        });

        mesh.addTo(app);
        micObjects.push(mesh);
    }

}

export let settings = new Settings();
const app = new WHS.App([
    new WHS.ElementModule({
        container: document.getElementById('app')
    }),
    new WHS.SceneModule(),
    new WHS.DefineModule('camera', new WHS.PerspectiveCamera({
        position: new THREE.Vector3(61, 41, 0.5)
    })),
    new WHS.RenderingModule({
        bgColor: 0x162129,

        renderer: {
            antialias: true,
            shadowmap: {
                type: THREE.PCFSoftShadowMap
            }
        }
    }, { shadow: true }),
    new WHS.OrbitControlsModule(),
    new WHS.ResizeModule()
]);
const mic = new WHS.Importer({
    loader: new THREE.ObjectLoader(),
    parser(object: any, material: any) { // data from loader
        console.log(object);
        return object // should return your .native (mesh in this case)
    },
    url: `/models/mic.json`,
    position: {
        x: -15,
        y: 20,
        z: 0
    },
    scale: [8, 8, 8],
    rotation: {
        x: -Math.PI / 2,
        y: 0,
        z: 0
    },
    shadow: true,
    material: new THREE.MeshPhongMaterial({
        color: 0x696969
    }),
    modules: [
        new WHS.TextureModule({
            url: `/images/micTexture.png`
        })
    ]
});
const table = new WHS.Importer({
    loader: new THREE.ObjectLoader(),
    parser(object: any, material: any) { // data from loader
        console.log(object);
        return object // should return your .native (mesh in this case)
    },
    url: `/models/table.json`,
    position: {
        x: 0,
        y: 0,
        z: 0
    },
    scale: [0.2, 0.2, 0.2],
    rotation: {
        x: -Math.PI / 2,
        y: 0,
        z: 0
    },
    shadow: true,
    material: new THREE.MeshPhongMaterial({
        color: 0x696969
    }),
    modules: [
        new WHS.TextureModule({
            url: `/images/tableTexture.jpg`
        })
    ]
});

let micObjects: Array<any> = [];
