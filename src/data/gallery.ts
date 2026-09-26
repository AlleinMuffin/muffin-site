/**
 * 服务器相册（首页杂志式布局 + /mcserver 完整版都读这份数据）。
 * 换成真实截图时：把图片放进 public/gallery/，改这里的 src / alt / caption 即可，
 * 建议导出 WebP 或 JPG（SVG 体积大，且部分平台不支持做分享缩略图）。
 */
export interface GalleryImage {
  src: string;
  alt: string;
  caption: string;
}

export const gallery: GalleryImage[] = [
  {
    src: "/gallery/gallery-01.svg",
    alt: "服务器港口城市夜景",
    caption: "港口夜景 · Skyline from the harbour",
  },
  {
    src: "/gallery/gallery-02.svg",
    alt: "黎明时分的山脉",
    caption: "黎明山脉 · Mountain range at dawn",
  },
  {
    src: "/gallery/gallery-03.svg",
    alt: "洞穴中的发光晶簇",
    caption: "深洞晶簇 · Deep cave crystals",
  },
  {
    src: "/gallery/gallery-04.svg",
    alt: "水面上的要塞",
    caption: "水上要塞 · Fortress over the water",
  },
  {
    src: "/gallery/gallery-05.svg",
    alt: "信标大厅的光柱",
    caption: "信标大厅 · Beacon hall",
  },
  {
    src: "/gallery/gallery-06.svg",
    alt: "黄昏时的梯田农场",
    caption: "黄昏梯田 · Terraced fields at dusk",
  },
];
